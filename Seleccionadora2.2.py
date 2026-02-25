 
from ctypes import HRESULT
import cv2
import serial
import io
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

#HR = 1920
#VR = 1080

cap.set(3, HR)  # Resolución horizontal
cap.set(4, VR)  # Resolución vertical

# Captura un primer frame de prueba para verificar la cámara
ret, frame1 = cap.read()
print("--- %s seconds ---" % (time.time() - start_time))
print("shape", frame1.shape)
print("size",  frame1.size)
print("dtype", frame1.dtype)

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
    cnts, hierarchy = cv2.findContours(morpho(mask), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
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
    cv2.createTrackbar('brillo',   'Parametros', 85,             255,  nada)
    cv2.createTrackbar('focus',    'Parametros', 0,              50,   nada)
    cv2.createTrackbar('H_min',    'Parametros', 9,              179,  nada)
    cv2.createTrackbar('H_max',    'Parametros', 34,             179,  nada)
    cv2.createTrackbar('S_min',    'Parametros', 121,            255,  nada)
    cv2.createTrackbar('S_max',    'Parametros', 179,            255,  nada)
    cv2.createTrackbar('V_min',    'Parametros', 109,            255,  nada)
    cv2.createTrackbar('V_max',    'Parametros', 226,            255,  nada)
    # Nuevo slider: área mínima del contorno (px²) para filtrar ruido
    cv2.createTrackbar('area_min', 'Parametros', AREA_MIN_INIT,  5000, nada)

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
        cap.set(cv2.CAP_PROP_BRIGHTNESS, cv2.getTrackbarPos('brillo',   'Parametros'))
        cap.set(28,                      cv2.getTrackbarPos('focus',    'Parametros'))
        area_min = cv2.getTrackbarPos('area_min', 'Parametros')  # Área mínima desde slider
    else:
        area_min = AREA_MIN_INIT  # Valor fijo si no hay ventana de parámetros

    # ── Convertir a HSV y crear máscara para granos de café ──
    hsv         = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    mask_coffee = cv2.inRange(hsv, coffee_low, coffee_hi)

    # ── Detectar objetos y actualizar tracker ──
    puntos_cafe = find_object(im, mask_coffee, 'cafe', area_min)
    boxes_ids   = tracker.update(puntos_cafe)

    # ── Dibujar bounding boxes y disparar señal al Arduino ──
    for box_id in boxes_ids:
        x, y, w, h, col, id = box_id
        cx = (x + x + w) // 2   # Centro horizontal del bounding box
        cy = (y + y + h) // 2   # Centro vertical del bounding box
        color = (0, 165, 255)    # Naranja para granos de café

        # Si el objeto cruza la banda de detección (5%-10% del alto del frame)
        if VR * 0.05 < cy < VR * 0.1:
            if id not in object_sorted_ids:
                object_sorted_ids.add(id)   # Marcar como ya enviado
                print(object_sorted_ids)
                print('x=', cx)
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
_ = write_read('C0\n')       # Detener cinta antes de salir
cap.release()
cv2.destroyAllWindows()
print("--- %s seconds ---" % (time.time() - start_time))
