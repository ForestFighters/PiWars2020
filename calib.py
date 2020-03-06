#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
import time
import sys
import gpiozero
import numpy as np
import cv2 as cv
from PIL import Image
from camera import Camera
from argparse import ArgumentParser
import logging
import os
from rectangle import Rectangle 
from time import sleep

from picamera.array import PiRGBArray
from picamera.array import PiYUVArray

running = True
showMask = True

button = 0
	
def click(event, x, y, flags, param):
	global running, button
	
	exitRect = Rectangle(290,0,320,20)
	switchRect = Rectangle(310,220,350,240)
	
	if event == cv.EVENT_LBUTTONDOWN:
		print("x {0} - y {1}", x, y )
		
		if exitRect.Contains( x, y ):
			running = False	
			
		if switchRect.Contains( x, y ):
			button = 1	
	
def showMenuImage(menu_img):
	cv.imshow('image',menu_img)
	cv.waitKey(1)

def main():
	global running, button
	w = 320
	h = 240
		
	camera = Camera( w, h)
	
	camera.Rotate( 270 )

	cv.namedWindow('image', cv.WND_PROP_FULLSCREEN)
	cv.setWindowProperty('image',cv.WND_PROP_FULLSCREEN,cv.WINDOW_FULLSCREEN)	
	cv.setMouseCallback("image", click)	
	
	rawCapture = PiRGBArray( camera, size=(w, h))	
	time.sleep(0.1)
		
	lower = np.array([110,50,50])
	upper = np.array([130,255,255])
			
	showMask = True;
	for frame in camera.CaptureContinous(rawCapture):	
		if running == False:
			break;
						
		if button == 1:
			showMask = not showMask
			button = 0
			
		raw = frame.array						
		imgHSV = cv.cvtColor(raw, cv.COLOR_RGB2HSV)   # Convert the captured frame from RGB to HSV ( with blue in the red position )				
		imgMask = cv.inRange(imgHSV, lower, upper)	
		#kernel = np.ones((3,3), np.uint8)								
		#imgMask = cv.erode(imgMask, ke0rnel, iterations=2)
		#imgMask = cv.dilate(imgMask, kernel, iterations=4)
		imgMask = cv.erode(imgMask, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
		imgMask = cv.dilate(imgMask, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
		
		imgMask = cv.dilate(imgMask, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
		imgMask = cv.erode(imgMask, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)))
		
		if showMask:
			image = imgMask
		else:
			image = raw
		
		cv.rectangle(image,(290,0),(320,20),(255,255,255),-1);
		cv.putText(image, "X", (298, 18), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		
		cv.rectangle(image,(0,220),(40,240),(255,255,255),-1);
		cv.putText(image, "-H", (8, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		cv.rectangle(image,(50,220),(90,240),(255,255,255),-1);
		cv.putText(image, "+H", (58, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));		
		
		cv.rectangle(image,(100,220),(150,240),(255,255,255),-1);
		cv.putText(image, "-S", (108, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		cv.rectangle(image,(160,220),(200,240),(255,255,255),-1);
		cv.putText(image, "+S", (168, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		
		cv.rectangle(image,(210,220),(250,240),(255,255,255),-1);
		cv.putText(image, "-V", (218, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		cv.rectangle(image,(260,220),(300,240),(255,255,255),-1);
		cv.putText(image, "+V", (268, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		
		cv.rectangle(image,(310,220),(350,240),(255,255,255),-1);
		cv.putText(image, "+", (311, 236), cv.FONT_HERSHEY_PLAIN, 1, (0,0,0));
		
		text = "{0} {1}".format(lower, upper)
		cv.putText(image, text,(10, 20), cv.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)					
		showMenuImage(image)		
		rawCapture.truncate(0)	
		
	cv.destroyAllWindows()
		
if __name__ == '__main__':
	main()
