 
from ctypes import HRESULT
import cv2
import serial
import io
import numpy as np
from time import sleep
import time
from tracker import * 
#https://www.youtube.com/watch?v=O3b8lVF93jU&t=3s


start_time = time.time()
arduino = serial.Serial(port='COM3', baudrate=115200, timeout=.1) #https://create.arduino.cc/projecthub/ansh2919/serial-communication-between-python-and-arduino-e7cce0
#https://www.youtube.com/watch?v=g4_SpZGaszY
tracker = EuclideanDistTracker()
object_sorted_ids = set()

### https://www.youtube.com/watch?v=oR71RSulTkQ

# Cafe (Quaker) - valores calibrados desde imagen de referencia
coffee_low = np.array([9,  121, 109], np.uint8)
coffee_hi  = np.array([34, 179, 226], np.uint8)
Parametros=1
RESIZE_RATIO = 0.25

#cap = cv2.VideoCapture('Seleccionadora1.mp4')
#cap = cv2.VideoCapture('maxSpeed1.mp4')
#cap = cv2.VideoCapture('maxSpeed2.mp4')
#cap = cv2.VideoCapture('mediumspeed.mp4')

#cap = cv2.VideoCapture('caida.mp4')

####################################### Camera############################
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) # turn the autofocus off
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
#cap.set(cv2.CAP_P, 20)

focus = 4 
cap.set(28, focus)
 
#cap.set(cv2.CAP_PROP_BRIGHTNESS, 20)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 20)
#cap.set(cv2.CAP_PROP_EXPOSURE, -6)
cap.set(cv2.CAP_PROP_EXPOSURE, -6)

HR = 640
VR = 360 

#HR = 1280
#VR = 720

#HR = 1920
#VR = 1080


cap.set(3, HR) # set the Horizontal resolution 
cap.set(4, VR) # Set the Vertical resolution

####################################### Camera############################

ret, frame1 = cap.read()
#im=img[340:720,500:800]
print("--- %s seconds ---" % (time.time() - start_time))
print ("shape",frame1.shape)
print ("size",frame1.size)
print ("dtype",frame1.dtype)

def write_read(x):
	arduino.write(bytes(x, 'utf-8'))
    #arduino.write(b"izq1\n")

	#arduino.flush()
	time.sleep(0.05)
	data = arduino.readline()
	return data

def nada(x):
    pass

def morpho(src):
	kernel = np.ones((3,3),np.uint8)
	open=cv2.morphologyEx(src,cv2.MORPH_OPEN,kernel)
	close=cv2.morphologyEx(open,cv2.MORPH_CLOSE,kernel)
	return close

def find_object(im, mask, col):
    cnts, hierarchy = cv2.findContours(morpho(mask), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    detections = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 150:
            x, y, w, h = cv2.boundingRect(c)
            detections.append([x, y, w, h, col])
    return detections

if Parametros==1:
    cv2.namedWindow('Parametros')
    cv2.createTrackbar('brillo',  'Parametros', 85,  255, nada)
    cv2.createTrackbar('focus',   'Parametros', 0,   50,  nada)
    cv2.createTrackbar('H_min',   'Parametros', 9,   179, nada)
    cv2.createTrackbar('H_max',   'Parametros', 34,  179, nada)
    cv2.createTrackbar('S_min',   'Parametros', 121, 255, nada)
    cv2.createTrackbar('S_max',   'Parametros', 179, 255, nada)
    cv2.createTrackbar('V_min',   'Parametros', 109, 255, nada)
    cv2.createTrackbar('V_max',   'Parametros', 226, 255, nada)
while (cap.isOpened()):
    #cv2.getTrackbarPos('exposure','Parametros')
    #cap.set(cv2.CAP_PROP_EXPOSURE,cv2.getTrackbarPos('expo','Parametros'))
    
    
    ret, img = cap.read()
    if ret == False:
        break
    #(h, w) = im.shape[:2]
    #im = cv2.resize(im, (int(w * RESIZE_RATIO), int(h * RESIZE_RATIO)), interpolation=cv2.INTER_CUBIC)
    im=img[0:VR,0:int(HR*1)]

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
        cap.set(cv2.CAP_PROP_BRIGHTNESS, cv2.getTrackbarPos('brillo', 'Parametros'))
        cap.set(28, cv2.getTrackbarPos('focus', 'Parametros'))



    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    mask_coffee = cv2.inRange(hsv, coffee_low, coffee_hi)

    puntos_cafe = find_object(im, mask_coffee, 'cafe')
    boxes_ids = tracker.update(puntos_cafe)

    for box_id in boxes_ids:
        x, y, w, h, col, id = box_id
        cx = (x + x + w) // 2
        cy = (y + y + h) // 2
        color = (0, 165, 255)  # naranja para granos de cafe
        if VR * 0.05 < cy < VR * 0.1:
            if id not in object_sorted_ids:
                object_sorted_ids.add(id)
                print(object_sorted_ids)
                print('x=', cx)
                value = write_read('M' + str(int(cx / 17)) + '\n')
                print('arduino dice:', value)

        cv2.putText(im, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.rectangle(im, (x, y), (x + w, y + h), color, 1)

    cv2.imshow('Image',im)
    #print (object_sorted_ids)

    

    cv2.imshow('Mask Coffee', mask_coffee)
    
    key = cv2.waitKey(1)
    if key==27:
        break
    elif key== ord('n'):
        value = write_read('C1\n')
        print ('arduino dice:',value)
        
    elif key== ord('m'):
        value = write_read('C0\n')
        print ('arduino dice:',value)
    elif key== ord('t'):
        value = write_read('T1\n')
        print ('arduino dice:',value)
    elif key== ord('p'):
        value = write_read('T0\n')
        print ('arduino dice:',value)
    elif key== ord('k'):
        value = write_read('M34\n')
        print ('arduino dice:',value)
    elif key== ord('l'):
        value = write_read('M5\n')
        print ('arduino dice:',value)
    elif key== ord('h'):
        for z in range(35):
            value = write_read('M'+str(z)+'\n')
            print ('arduino dice:',value)
            sleep(2 )

    #sleep(0.3)

_ = write_read('C0\n')
cap.release()
cv2.destroyAllWindows()
print("--- %s seconds ---" % (time.time() - start_time))
