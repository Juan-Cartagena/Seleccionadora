 
from ctypes import HRESULT
import cv2
import serial
import io
import json
import os
import numpy as np
from time import sleep
import time
from tracker import * 
#https://www.youtube.com/watch?v=O3b8lVF93jU


start_time = time.time()

# ──────────────────────────────────────────────────────────────
# Conexión serie con Arduino
# Referencia: https://create.arduino.cc/projecthub/ansh2919/serial-communication-between-python-and-arduino-e7cce0
# ──────────────────────────────────────────────────────────────
arduino = serial.Serial(port='COM3', baudrate=115200, timeout=.1)

# Tracker de objetos basado en distancia euclidiana
# Referencia: https://www.youtube.com/watch?v=g4_SpZGaszY
tracker = EuclideanDistTracker()

# Conjunto de IDs ya enviados al Arduino (para no repetir la señal)
object_sorted_ids = set()

### Referencia detección de color: https://www.youtube.com/watch?v=oR71RSulTkQ

# ──────────────────────────────────────────────────────────────
# Rango HSV inicial para granos de café (Quaker / defectuoso)
# Estos valores se sobrescriben en tiempo real con los sliders
# ──────────────────────────────────────────────────────────────
coffee_low = np.array([9,  121, 109], np.uint8)
coffee_hi  = np.array([34, 179, 226], np.uint8)

# Área mínima inicial de contorno (px²) para considerar un objeto válido
AREA_MIN_INIT = 40

# Bandera para mostrar/activar la ventana de parámetros ajustables
Parametros = 1

# Factor de redimensionado (no usado actualmente, reservado para pruebas)
RESIZE_RATIO = 0.5

# ──────────────────────────────────────────────────────────────
# Captura de video
# Descomenta la línea del archivo de video que quieras usar para pruebas
# ──────────────────────────────────────────────────────────────
#cap = cv2.VideoCapture('Seleccionadora1.mp4')
#cap = cv2.VideoCapture('maxSpeed1.mp4')
#cap = cv2.VideoCapture('maxSpeed2.mp4')
#cap = cv2.VideoCapture('mediumspeed.mp4')
#cap = cv2.VideoCapture('caida.mp4')

# Cámara en vivo (índice 0, backend DirectShow para Windows)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# ──────────────────────────────────────────────────────────────
# Configuración de la cámara
# ──────────────────────────────────────────────────────────────
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)    # Desactivar autoenfoque
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0) # Desactivar exposición automática

focus = 4                   # Valor inicial de foco manual
cap.set(28, focus)          # CAP_PROP_FOCUS (índice 28)

cap.set(cv2.CAP_PROP_BRIGHTNESS, 20)  # Brillo inicial
cap.set(cv2.CAP_PROP_EXPOSURE, -6)    # Exposición inicial

# Resolución horizontal y vertical
HR = 640
VR = 360 

#HR = 1280
#VR = 720

# HR = 1920
# VR = 1080

cap.set(3, HR)  # Resolución horizontal
cap.set(4, VR)  # Resolución vertical

# Captura un primer frame de prueba para verificar la cámara
ret, frame1 = cap.read()
print("--- %s seconds ---" % (time.time() - start_time))
print("shape", frame1.shape)
print("size",  frame1.size)
print("dtype", frame1.dtype)

# ──────────────────────────────────────────────────────────────
# Persistencia de parámetros: guardar/cargar sliders en JSON
# El archivo se crea en la misma carpeta que este script
# ──────────────────────────────────────────────────────────────
PARAMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parametros.json')

DEFAULT_PARAMS = {
    'brillo':       85,
    'focus':        0,
    'H_min':        9,
    'H_max':        34,
    'S_min':        121,
    'S_max':        179,
    'V_min':        109,
    'V_max':        226,
    'area_min':     40,
    'linea_meta':   1,
    'zona_top':     5,   # % del alto del frame → borde superior de la banda de detección
    'zona_bot':     10,  # % del alto del frame → borde inferior de la banda de detección
    'disparo_delay': 0,  # ms de espera antes de enviar la señal al Arduino
}

def cargar_params():
    """Lee parametros.json; si no existe devuelve los valores por defecto."""
    if os.path.isfile(PARAMS_FILE):
        try:
            with open(PARAMS_FILE, 'r') as f:
                data = json.load(f)
            # Rellenar claves faltantes con defaults (compatibilidad hacia atrás)
            for k, v in DEFAULT_PARAMS.items():
                data.setdefault(k, v)
            print('Parámetros cargados desde', PARAMS_FILE)
            return data
        except Exception as e:
            print('Error leyendo parametros.json, usando defaults:', e)
    return dict(DEFAULT_PARAMS)

def guardar_params(p):
    """Escribe el diccionario p en parametros.json."""
    try:
        with open(PARAMS_FILE, 'w') as f:
            json.dump(p, f, indent=4)
        print('Parámetros guardados en', PARAMS_FILE)
    except Exception as e:
        print('Error guardando parametros.json:', e)

# Cargar valores al inicio (o usar defaults la primera vez)
params = cargar_params()

# ──────────────────────────────────────────────────────────────
# Función: enviar comando al Arduino y leer respuesta
# ──────────────────────────────────────────────────────────────
def write_read(x):
	arduino.write(bytes(x, 'utf-8'))  # Enviar string como bytes
	time.sleep(0.05)                  # Pequeña espera para asegurar transmisión
	data = arduino.readline()         # Leer respuesta del Arduino
	return data

# ──────────────────────────────────────────────────────────────
# Callback vacío requerido por createTrackbar cuando no se
# necesita ejecutar nada al mover el slider
# ──────────────────────────────────────────────────────────────
def nada(x):
    pass

# ──────────────────────────────────────────────────────────────
# Función: aplicar operaciones morfológicas para limpiar la máscara
# Se usa apertura (elimina ruido pequeño) seguida de cierre
# (rellena huecos internos en los objetos)
# ──────────────────────────────────────────────────────────────
def morpho(src):
	kernel = np.ones((3,3), np.uint8)
	open  = cv2.morphologyEx(src, cv2.MORPH_OPEN,  kernel)
	close = cv2.morphologyEx(open, cv2.MORPH_CLOSE, kernel)
	return close

# ──────────────────────────────────────────────────────────────
# Función: detectar objetos en la máscara y devolver sus
# bounding boxes junto con la etiqueta de color/clase
#   im   – frame original (no se modifica aquí)
#   mask – máscara binaria del color de interés
#   col  – etiqueta de clase (e.g. 'cafe')
#   area_min – área mínima en px² para considerar un contorno válido
# ──────────────────────────────────────────────────────────────
def find_object(im, mask, col, area_min=40):
    cnts, hierarchy = cv2.findContours(morpho(mask), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    detections = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area > area_min:                          # Filtrar contornos pequeños (ruido)
            x, y, w, h = cv2.boundingRect(c)
            detections.append([x, y, w, h, col])    # Guardar bounding box y clase
    return detections

# ──────────────────────────────────────────────────────────────
# Crear ventana de sliders si Parametros == 1
# ──────────────────────────────────────────────────────────────
if Parametros == 1:
    cv2.namedWindow('Parametros')
    cv2.resizeWindow('Parametros', 600, 550)  # Ancho x Alto — agrandado para los sliders nuevos
    # Los valores iniciales vienen del archivo parametros.json (o defaults si es la primera vez)
    cv2.createTrackbar('brillo',        'Parametros', params['brillo'],        255, nada)
    cv2.createTrackbar('focus',         'Parametros', params['focus'],         50,  nada)
    cv2.createTrackbar('H_min',         'Parametros', params['H_min'],         179, nada)
    cv2.createTrackbar('H_max',         'Parametros', params['H_max'],         179, nada)
    cv2.createTrackbar('S_min',         'Parametros', params['S_min'],         255, nada)
    cv2.createTrackbar('S_max',         'Parametros', params['S_max'],         255, nada)
    cv2.createTrackbar('V_min',         'Parametros', params['V_min'],         255, nada)
    cv2.createTrackbar('V_max',         'Parametros', params['V_max'],         255, nada)
    cv2.createTrackbar('area_min',      'Parametros', params['area_min'],      500, nada)
    cv2.createTrackbar('linea_meta',    'Parametros', params['linea_meta'],    1,   nada)
    # ── Nuevos sliders de zona y delay ──
    cv2.createTrackbar('zona_top %',    'Parametros', params['zona_top'],      100, nada)  # Borde superior (% del alto)
    cv2.createTrackbar('zona_bot %',    'Parametros', params['zona_bot'],      100, nada)  # Borde inferior (% del alto)
    cv2.createTrackbar('disparo_delay', 'Parametros', params['disparo_delay'], 500, nada)  # Delay disparo (ms)

# ──────────────────────────────────────────────────────────────
# Bucle principal de captura y procesamiento
# ──────────────────────────────────────────────────────────────
while (cap.isOpened()):

    ret, img = cap.read()
    if ret == False:
        break

    # Recortar región de interés (ROI) — actualmente el frame completo
    im = img[0:VR, 0:int(HR * 1)]

    # ── Leer sliders y actualizar parámetros en tiempo real ──
    if Parametros == 1:
        coffee_low = np.array([
            cv2.getTrackbarPos('H_min', 'Parametros'),
            cv2.getTrackbarPos('S_min', 'Parametros'),
            cv2.getTrackbarPos('V_min', 'Parametros')
        ], np.uint8)
        coffee_hi = np.array([
            cv2.getTrackbarPos('H_max', 'Parametros'),
            cv2.getTrackbarPos('S_max', 'Parametros'),
            cv2.getTrackbarPos('V_max', 'Parametros')
        ], np.uint8)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, cv2.getTrackbarPos('brillo',     'Parametros'))
        cap.set(28,                      cv2.getTrackbarPos('focus',      'Parametros'))
        area_min      = cv2.getTrackbarPos('area_min',      'Parametros')  # Área mínima desde slider
        linea_meta    = cv2.getTrackbarPos('linea_meta',    'Parametros')  # 1 = mostrar línea, 0 = ocultar
        zona_top_pct  = cv2.getTrackbarPos('zona_top %',   'Parametros')  # Borde superior de detección (%)
        zona_bot_pct  = cv2.getTrackbarPos('zona_bot %',   'Parametros')  # Borde inferior de detección (%)
        disparo_delay = cv2.getTrackbarPos('disparo_delay','Parametros')  # Delay antes del disparo (ms)
    else:
        area_min      = AREA_MIN_INIT
        linea_meta    = 0
        zona_top_pct  = 5
        zona_bot_pct  = 10
        disparo_delay = 0

    # Convertir porcentajes a píxeles
    y_top = int(VR * zona_top_pct / 100)
    y_bot = int(VR * zona_bot_pct / 100)

    # ── Convertir a HSV y crear máscara para granos de café ──
    hsv         = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    mask_coffee = cv2.inRange(hsv, coffee_low, coffee_hi)

    # ── Dibujar línea de meta si el checkbox está activo ──
    if linea_meta == 1:
        cv2.line(im, (0, y_top), (HR, y_top), (255, 255, 255), 1)  # Línea superior de la zona
        cv2.line(im, (0, y_bot), (HR, y_bot), (255, 255, 255), 1)  # Línea inferior de la zona

    # ── Detectar objetos y actualizar tracker ──
    puntos_cafe = find_object(im, mask_coffee, 'cafe', area_min)
    boxes_ids   = tracker.update(puntos_cafe)

    # ── Dibujar bounding boxes y disparar señal al Arduino ──
    for box_id in boxes_ids:
        x, y, w, h, col, id = box_id
        cx = (x + x + w) // 2   # Centro horizontal del bounding box
        cy = (y + y + h) // 2   # Centro vertical del bounding box
        color = (0, 165, 255)    # Naranja para granos de café

        # Si el objeto cruza la banda de detección (controlada por sliders zona_top/zona_bot)
        if y_top < cy < y_bot:
            if id not in object_sorted_ids:
                object_sorted_ids.add(id)   # Marcar como ya enviado
                print(object_sorted_ids)
                print('x=', cx)
                # Esperar el delay configurado antes de disparar
                if disparo_delay > 0:
                    time.sleep(disparo_delay / 1000.0)
                # Enviar posición al Arduino (escala de 0-37 aprox.)
                value = write_read('M' + str(int(cx / 17)) + '\n')
                print('arduino dice:', value)

        # Dibujar ID del objeto y rectángulo
        cv2.putText(im, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.rectangle(im, (x, y), (x + w, y + h), color, 1)

    # ── Mostrar ventanas de debug ──
    cv2.imshow('Image', im)
    cv2.imshow('Mask Coffee', mask_coffee)

    # ── Manejo de teclas ──
    key = cv2.waitKey(1)
    if key == 27:                        # ESC → salir
        break
    elif key == ord('n'):                # n → activar cinta
        value = write_read('C1\n')
        print('arduino dice:', value)
    elif key == ord('m'):                # m → detener cinta
        value = write_read('C0\n')
        print('arduino dice:', value)
    elif key == ord('t'):                # t → test ON
        value = write_read('T1\n')
        print('arduino dice:', value)
    elif key == ord('p'):                # p → test OFF
        value = write_read('T0\n')
        print('arduino dice:', value)
    elif key == ord('k'):                # k → mover a posición 34
        value = write_read('M34\n')
        print('arduino dice:', value)
    elif key == ord('l'):                # l → mover a posición 5
        value = write_read('M5\n')
        print('arduino dice:', value)
    elif key == ord('h'):                # h → barrer todas las posiciones (test)
        for z in range(35):
            value = write_read('M' + str(z) + '\n')
            print('arduino dice:', value)
            sleep(2)

# ──────────────────────────────────────────────────────────────
# Limpieza al cerrar
# ──────────────────────────────────────────────────────────────

# Guardar valores actuales de los sliders antes de salir
if Parametros == 1:
    params_guardados = {
        'brillo':        cv2.getTrackbarPos('brillo',        'Parametros'),
        'focus':         cv2.getTrackbarPos('focus',         'Parametros'),
        'H_min':         cv2.getTrackbarPos('H_min',        'Parametros'),
        'H_max':         cv2.getTrackbarPos('H_max',        'Parametros'),
        'S_min':         cv2.getTrackbarPos('S_min',        'Parametros'),
        'S_max':         cv2.getTrackbarPos('S_max',        'Parametros'),
        'V_min':         cv2.getTrackbarPos('V_min',        'Parametros'),
        'V_max':         cv2.getTrackbarPos('V_max',        'Parametros'),
        'area_min':      cv2.getTrackbarPos('area_min',     'Parametros'),
        'linea_meta':    cv2.getTrackbarPos('linea_meta',   'Parametros'),
        'zona_top':      cv2.getTrackbarPos('zona_top %',   'Parametros'),
        'zona_bot':      cv2.getTrackbarPos('zona_bot %',   'Parametros'),
        'disparo_delay': cv2.getTrackbarPos('disparo_delay','Parametros'),
    }
    guardar_params(params_guardados)

_ = write_read('C0\n')       # Detener cinta antes de salir
cap.release()
cv2.destroyAllWindows()
print("--- %s seconds ---" % (time.time() - start_time))
