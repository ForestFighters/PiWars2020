#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
import time
import sys
import gpiozero
import numpy as np
import cv2 as cv
#import picamera.array 
from PIL import Image
from camera import Camera
from robot import Robot
from approxeng.input.selectbinder import ControllerResource
from argparse import ArgumentParser
import logging
import os
from time import sleep

#from picamera import PiCamera
from picamera.array import PiRGBArray
from picamera.array import PiYUVArray


seconds = lambda: int(round(time.time()))

INTERVAL = 0.0

LOGGER = logging.getLogger(__name__)

class Controller():
	mode = None
		
	def __init__(self):
				
		self.last_text = ''		 
		self.bot = Robot()
		interval = 0.0
		
		self.w = 320
		self.h = 240
		
		self.camera = Camera(self.w, self.h)		
		super().__init__()
		

	def run(self):  
		self.show('Started')	
		cv.namedWindow('image', cv.WND_PROP_FULLSCREEN)
		cv.setWindowProperty('image',cv.WND_PROP_FULLSCREEN,cv.WINDOW_FULLSCREEN)	
		menu_img = self.loadMenuImage('/home/pi/Pictures/Menu.jpg')
		notfound_img = self.loadMenuImage('/home/pi/Pictures/Joystick.jpg')
		camera_img = self.loadMenuImage('/home/pi/Pictures/Camera.jpg')
		remote_img = self.loadMenuImage('/home/pi/Pictures/Remote-Controlled.jpg')
		lava_img = self.loadMenuImage('/home/pi/Pictures/Lava-Palava.jpg')
		mine_img = self.loadMenuImage('/home/pi/Pictures/Minesweeper.jpg')
		maze_img = self.loadMenuImage('/home/pi/Pictures/Maze.jpg')
		exit_img = self.loadMenuImage('/home/pi/Pictures/Exit.jpg')
		halt_img = self.loadMenuImage('/home/pi/Pictures/Halt.jpg')				
		gear = 2
		menu = 1		
		MIN_MENU = 1
		MAX_MENU = 6
		
		running = True
		timing = 20000		
				
		while running:	  
			try:
				self.show('Press CTRL+C to quit')
				self.showMenuImage(menu_img)
				cv.waitKey(1)
				with ControllerResource() as joystick: 
					if joystick.connected :
						# Set previous menu item
						prev = 0	
						menu = 1				
						# Loop indefinitely						
						while running:							
							presses = joystick.check_presses()							
							if presses.select:
								# Ensure we have the camera attached for this challenges
								if (menu == 2 or menu == 3 or menu == 4) and (self.camera.hasCamera == False):
									self.showMenuImage(camera_img)									
								else:
									self.showMenuImage(menu_img)
									running = self.doMenu( menu, joystick, gear )								
									prev = 0							
																
							if joystick.presses.dright:
								menu += 1                   
								if menu > MAX_MENU:
									menu = MIN_MENU
										
							if joystick.presses.dleft:
								menu -= 1
								if menu < MIN_MENU:
									menu = MAX_MENU
								
							if prev != menu:
								#print(" Menu = {}".format(menu))
												
								if menu == 1:
									self.showMenuImage(remote_img)			
								if menu == 2:						
									self.showMenuImage(lava_img)												
								if menu == 3:			
									self.showMenuImage(mine_img)												
								if menu == 4:			
									self.showMenuImage(maze_img)												
								if menu == 5:			
									self.showMenuImage(exit_img)												
								if menu == 6:
									self.showMenuImage(halt_img)									
									
							prev = menu 								

																		
																					
							# Select menu option                    
							# time.sleep(INTERVAL)
			
			except IOError:
					LOGGER.info('Unable to find joystick')
					self.showMenuImage(notfound_img)
					time.sleep(4.0)
					
			except KeyboardInterrupt:
				# CTRL+C exit, disable all drives
				self.bot.move(0, 0)
				self.show('Motors off')
				break
				
		cv.destroyAllWindows()
		
	def doMenu(self, menu, joystick, gear ):
		if menu == 1:
			self.remoteNoCamera( joystick, gear )	
			return True
		if menu == 2:			
			self.straight( joystick, gear )
			return True
		if menu == 3:			
			self.mine( joystick, gear )
			return True
		if menu == 4:			
			self.maze( joystick, gear )
			return True
		if menu == 5:			
			return False
		if menu == 6:
			self.shutdown()
			# We don't expect to get here
			return False			
			
	def shutdown(self):
		self.show("Shutdown")		
		os.system("sudo halt")		
				
				
	# Pi Noon, Zombie Shoot, Temple of Doom, Eco Disaster	
	def remoteNoCamera(self, joystick, gear):
		self.show("Remote no Camera mode")
			
		self.bot.servo_off()	
		count = 0 	
		while True:		
			presses = joystick.check_presses()
			if presses.home:
				#self.show('HOME pressed since last check')
				running = False
				break
			
			count += 1
			left_drive = joystick.ly
			right_drive = joystick.ry									
			self.bot.move(left_drive, right_drive, gear)
						
			if joystick.presses.cross:
				self.bot.trigger( 90 ) 
				time.sleep(0.25) 				                 
			if joystick.presses.triangle:
				self.bot.trigger( -90 )
				time.sleep(0.25) 
			if joystick.presses.dup:
				self.bot.tilt( 30 )                   
				time.sleep(0.25) 
			if joystick.presses.ddown:
				self.bot.tilt( -30 )	
				time.sleep(0.25) 
				
			self.bot.servo_off()			                 
			
				
			prev = gear
			if joystick.presses.l1:
				gear += 0.5								
			if joystick.presses.r1:									
				gear -= 0.5
											
			if gear < 1:
				gear = 1
			if gear > 5:
				gear = 5
				
			if gear != prev:				
				print(" Gear = {}".format(gear))
							
			self.bot.move(left_drive, right_drive, gear)	
			
		self.bot.stop()	
		
	def remoteWithCamera(self, joystick, gear):
		self.show("Remote with Camera mode")
		
		if self.camera.hasCamera == False:
			return
		
		rawCapture = PiRGBArray( self.camera, size=(self.w, self.h))	
		time.sleep(0.1)
				
		count = 0 	
		for frame in self.camera.CaptureContinous(rawCapture):		
			presses = joystick.check_presses()
			if presses.home:
				#self.show('HOME pressed since last check')
				running = False
				break
			
			image = frame.array	
							
			
			heading, roll, pitch = self.bot.readEuler()
			distance = self.bot.getDistance()
			count = 0
			text = "gear={0} : angle={1:5.2} : mm={2}".format(gear, heading, distance)
			cv.putText(image,text,(10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))			
		
			count += 1
			left_drive = joystick.ly
			right_drive = joystick.ry									
			self.bot.move(left_drive, right_drive, gear)
			
			if joystick.presses.cross:
				self.bot.trigger( 90 )  				                 
			if joystick.presses.triangle:
				self.bot.trigger( -90 )

			if joystick.presses.dup:
				self.bot.tilt( -10 )                   
			if joystick.presses.ddown:
				self.bot.tilt( 10 )

			if joystick.presses.dright:
				self.bot.pan( -5 )                   
			if joystick.presses.dleft:
				self.bot.pan( 5 )
				
			prev = gear
			if joystick.presses.l1:
				gear += 0.5								
			if joystick.presses.r1:									
				gear -= 0.5
											
			if gear < 1:
				gear = 1
			if gear > 5:
				gear = 5
				
			#if gear != prev:
			#	print(" Gear = {}".format(gear))
				
			self.showMenuImage(image)		
			rawCapture.truncate(0)	
			self.bot.move(left_drive, right_drive, gear)	
			
		self.bot.stop()		

	def maze(self, joystick, gear):
		self.show("Escape Route mode")
		
		if self.camera.hasCamera == False:			
			return
				
		rawCapture = PiRGBArray( self.camera, size=(self.w, self.h))	
		time.sleep(0.1)
		
		# State 0		
		# Travel until 276
		
		# State 1
		# Turn to 90
		
		# State 2
		# Travel until 174
		
		# State 3
		# Turn to 180 
		
		# State 4
		# Travel until 276
		
		# State 5
		# Turn to 90
		
		# State 6
		# Travel until 174
		
		# State 7
		# Turn to 0
		
		# State 8
		# Travel to 276
		
		# State 9
		# Turn to 90
		
		# State 10
		# Travel until 100
			
		firsttime = True
		offset = 0
		gear = 2
		state = 0 
		running = False
		count = 0 	
		for frame in self.camera.CaptureContinous(rawCapture):		
			presses = joystick.check_presses()
			if presses.home:				
				running = False
				break					
			
			if presses.start:
				running = True
				
			image = frame.array	
			
			# Read the Euler angles for heading, roll, pitch (all in degrees).
			heading, roll, pitch = self.bot.readEuler()			
			distance = self.bot.getDistance()
			
			# If heading just less than 360 then create an offset
			if firsttime and heading > 270:
				offset = 360 - heading
				firsttime = False
			
			heading += offset
			
			text = "state={0} : angle={1:5.2} : mm={2}".format(state, heading, distance)
			cv.putText(image,text,(10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))			
		
			self.showMenuImage(image)		
			rawCapture.truncate(0)	
			
			if running:
				if state == 0 and distance < 276:
					left_drive = 1
					right_drive = 1					
					state = 1
				elif state == 1 and heading < 90:
					left_drive = -0.5
					right_drive = +0.5
					state = 2				
				elif state == 2 and distance < 174:
					left_drive = 1
					right_drive = 1	
					state = 3
				elif state == 3 and heading < 180:
					left_drive = -0.5
					right_drive = +0.5
					state = 4				
				elif state == 3 and distance < 100:
					running = False
					break				
				
				self.bot.move(left_drive, right_drive, gear)
			
			self.bot.getInterval()	
			
		self.bot.stop()
		cv.namedWindow('image', cv.WND_PROP_FULLSCREEN)
		cv.setWindowProperty('image',cv.WND_PROP_FULLSCREEN,cv.WINDOW_FULLSCREEN)	
		cv.waitKey(10)
				
	def mine(self, joystick, gear):
		self.show("Mine Sweeper mode")
		
		if self.camera.hasCamera == False:
			return
		
		hw = int(self.w//2)
		hh = int(self.h//2)
				
		rawCapture = PiRGBArray( self.camera, size=(self.w, self.h))	
		time.sleep(0.1)
		
		lower_red = np.array([21, 173, 92])
		upper_red = np.array([51, 203, 122])
		
		showMask = False	
		colour = np.array([0, 0, 0])
		
		brightness = self.camera.Brightness
		
		for frame in self.camera.CaptureContinous(rawCapture):
			presses = joystick.check_presses()
			
			yPos = self.h - int(((joystick.ly + 1) * self.h)/2)
			xPos = int(((joystick.lx + 1) * self.w)/2)
			
			yPos = min(self.h - 1, yPos)
			xPos = min(self.w - 1, xPos)
			
			brightness = self.camera.SetBrightness(int(((joystick.ry + 1) * 100) /2))
			
			if presses.home:				
				running = False
				return
			if presses.start:				
				running = False
				break
			if presses.triangle:
				showMask = True
			if presses.cross:
				showMask = False
			if presses.circle:
				colour = imgHSV[yPos, xPos];
				print("xPos,yPos: {0},{1}   Colour: {2}".format(xPos,yPos,colour))
				lower_red[0] = max(0,colour[0] - 10)
				upper_red[0] = min(179,colour[0] + 10)
				lower_red[1] = max(0,colour[1] - 10)
				upper_red[1] = min(255,colour[1] + 10)
				lower_red[2] = max(0,colour[2] - 20)
				upper_red[2] = min(255,colour[2] + 20)
											
				
			# Take image
			image = frame.array				
			# Convert to  HSV
			imgHSV = cv.cvtColor(image, cv.COLOR_BGR2HSV)
			if showMask:
				self.camera.SetBrightness(brightness)				
				imgMask = cv.inRange(imgHSV, lower_red, upper_red)
				self.showMenuImage(imgMask)		
			else:
				# Draw a circle at the joystick position
				cv.circle(image,(xPos,yPos), 3, (255,255,255), -1)				
				# Display for calibration
				self.showMenuImage(image)		
				
			rawCapture.truncate(0)	
			
		
		frameNo = 1.0;
		start = seconds()	
		for frame in self.camera.CaptureContinous(rawCapture):	
			
			presses = joystick.check_presses()
			if presses.home:				
				running = False
				break
				
			image = frame.array	
			# do stuff			
			imgHSV = cv.cvtColor(image, cv.COLOR_BGR2HSV)   # Convert the captured frame from BGR to HSV
			
			# define range of red color in HSV
			
			# Threshold the HSV image to get only red colors
			imgMask = cv.inRange(imgHSV, lower_red, upper_red)
			
			frameNo += 1								
			self.showMenuImage(imgMask)		
			rawCapture.truncate(0)	
	
		end = seconds()
		print("Frames: {0} in {1} seconds or {2} frames per second".format(frameNo, end-start, frameNo / (end-start)))

	def straight(self, joystick, gear):
		self.show("Lava Palava mode")
		
		if self.camera.hasCamera == False:
			return
		
		hw = int(self.w//2)
		hh = int(self.h//2)
				
		rawCapture = PiRGBArray( self.camera, size=(self.w, self.h))	
		time.sleep(0.1)
		
		running = False
		self.bot.servo_off()
		
		frameNo = 1.0;
		start = seconds()	
		for frame in self.camera.CaptureContinous(rawCapture):	
			
			presses = joystick.check_presses()
			if presses.home:				
				running = False
				break
							
			if presses.start:				
				running = True	
				
			if joystick.presses.l1:
				gear += 0.5								
			if joystick.presses.r1:									
				gear -= 0.5
											
			if gear < 1:
				gear = 1
			if gear > 5:
				gear = 5			
				
			image = frame.array	
			
			Blackline = cv.inRange(image, (0,0,0), (60,60,60))	
			kernel = np.ones((3,3), np.uint8)
			Blackline = cv.erode(Blackline, kernel, iterations=5)
			Blackline = cv.dilate(Blackline, kernel, iterations=9)	
			img_blk,contours_blk, hierarchy_blk = cv.findContours(Blackline.copy(),cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)
	
			contours_blk_len = len(contours_blk)
			if contours_blk_len > 0:	 
				blackbox = cv.minAreaRect(contours_blk[0])
			else:
				canditates=[]
				off_bottom = 0	   
				for con_num in range(contours_blk_len):		
					blackbox = cv2.minAreaRect(contours_blk[con_num])
					(x_min, y_min), (w_min, h_min), ang = blackbox		
					box = cv2.boxPoints(blackbox)
					(x_box,y_box) = box[0]
					if y_box > (h - 2) :		 
						off_bottom += 1
					canditates.append((y_box,con_num,x_min,y_min))		
					
				canditates = sorted(canditates)
				
				if off_bottom > 1:	    
					canditates_off_bottom=[]
					for con_num in range ((contours_blk_len - off_bottom), contours_blk_len):
						(y_highest,con_highest,x_min, y_min) = canditates[con_num]		
						total_distance = (abs(x_min - x_last)**2 + abs(y_min - y_last)**2)**0.5
						canditates_off_bottom.append((total_distance,con_highest))
							
					canditates_off_bottom = sorted(canditates_off_bottom)         
					(total_distance,con_highest) = canditates_off_bottom[0]         
					blackbox = cv2.minAreaRect(contours_blk[con_highest])	   
				elif contours_blk_len > 1:		
					(y_highest,con_highest,x_min, y_min) = canditates[contours_blk_len-1]		
					blackbox = cv2.minAreaRect(contours_blk[con_highest])	
				
				
			(x_min, y_min), (w_min, h_min), ang = blackbox
			if ang < -45 :
				ang = 90 + ang
			if w_min < h_min and ang > 0:	  
				ang = (90-ang)*-1
			if w_min > h_min and ang < 0:
				ang = 90 + ang	  
				
			setpoint = hw
			error = int(x_min - setpoint) 
			ang = int(ang)	 
			box = cv.boxPoints(blackbox)
			box = np.int0(box)
			cv.drawContours(image,[box],0,(0,0,255),3)	 			
			cv.line(image, (int(x_min),200 ), (int(x_min),250 ), (255,0,0),3)

			left_drive = 1.0
			if error < -4:
				left_drive = left_drive - ( -error / 170 )
			
			right_drive = 1.0	
			if error > 4:
				right_drive = right_drive - ( error / 170 )
						
			text = "g = {0} : l = {1:.2} : r = {2:.2}".format(gear, left_drive, right_drive)
			cv.putText(image,text,(10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))		
						
			if running:
				self.bot.turn(error, gear)			
			
			frameNo += 1								
			self.showMenuImage(image)		
			rawCapture.truncate(0)	
	
		self.bot.stop()
		end = seconds()
		print("Frames: {0} in {1} seconds or {2} frames per second".format(frameNo, end-start, frameNo / (end-start)))

	def showMenuImage(self, menu_img):
		cv.imshow('image',menu_img)
		cv.waitKey(2)
		
	def loadMenuImage(self, fileName):
		img = cv.imread(fileName,cv.IMREAD_COLOR)
		img = cv.resize(img,(1280,960), interpolation = cv.INTER_CUBIC)			
		return img
		
	def writePNG(self, filename, y_data):
		imgSize = (32,32)
		# Use the PIL raw decoder to read the data.
		# the 'F;16' informs the raw decoder that we are reading 
		# a little endian, unsigned integer 16 bit data.
		#Image.fromstring('L', imgSize, y_data, 'L', 'F;16')
		img = Image.fromarray(y_data)
		img.save(filename)

	def show(self, text):
		# Only log changed values
		if text != self.last_text:
			print(text)
			LOGGER.debug(text)
			self.last_text = text	

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    parser = ArgumentParser()
    args = parser.parse_args()

    controller = Controller()
    controller.run()
