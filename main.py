#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
import time
import sys
import gpiozero
import numpy
import cv2 as cv
import picamera.array 
from PIL import Image
from camera import Camera
from robot import Robot
from approxeng.input.selectbinder import ControllerResource
from argparse import ArgumentParser
import logging
import os
from time import sleep

from Adafruit_BNO055 import BNO055
import VL53L0X


seconds = lambda: int(round(time.time()))

INTERVAL = 0.0

LOGGER = logging.getLogger(__name__)

class Controller():
	mode = None
	hasCamera = False
	
	def __init__(self):
				
		self.last_text = ''		 
		self.bot = Robot()
		try:
			self.camera = Camera(32,32)
			self.hasCamera = True
		except:
		self.hasCamera = False

		interval = 0.0
				
		super().__init__()
		

	def run(self):  
		self.show('Started')	
		cv.namedWindow('image', cv.WND_PROP_FULLSCREEN)
		cv.setWindowProperty('image',cv.WND_PROP_FULLSCREEN,cv.WINDOW_FULLSCREEN)	
		menu_img = self.loadMenuImage('/home/pi/Pictures/Menu.jpg')
		notfound_img = self.loadMenuImage('/home/pi/Pictures/Joystick.jpg')
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
		
		try:	
			# Create a VL53L0X object
			tof = VL53L0X.VL53L0X()
			# Start ranging
			# tof.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
			tof.start_ranging(VL53L0X.VL53L0X_HIGH_SPEED_MODE)

			timing = tof.get_timing()
			if timing < 20000:
				timing = 20000
			print("Timing %d ms" % (timing/1000))
			hasTOF = True
		except:
			print("Problem init TOF")
			hasTOF = False

		# Raspberry Pi configuration with serial UART and RST connected to GPIO 18:
		bno = BNO055.BNO055(serial_port='/dev/serial0', rst=7)
		while True:
			try:
				bno.begin()
				break
			except:
				print("BNO Error")				
				#raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')
				
		# Print BNO055 software revision and other diagnostic data.
		sw, bl, accel, mag, gyro = bno.get_revision()
		print('Software version:   {0}'.format(sw))
		print('Bootloader version: {0}'.format(bl))
		print('Accelerometer ID:   0x{0:02X}'.format(accel))
		print('Magnetometer ID:    0x{0:02X}'.format(mag))
		print('Gyroscope ID:       0x{0:02X}\n'.format(gyro))
		
		while running:	  
			try:
				self.show('Press CTRL+C to quit')
				self.showMenuImage(menu_img)
				with ControllerResource() as joystick: 
					if joystick.connected :					
						# Loop indefinitely
						while running:
							presses = joystick.check_presses()							
							if presses.select:
								running = self.doMenu( menu, joystick, gear )
								
							prev = menu 
							if joystick.presses.dright:
								menu += 1                   
								if menu > MAX_MENU:
									menu = MIN_MENU
										
							if joystick.presses.dleft:
								menu -= 1
								if menu < MIN_MENU:
									menu = MAX_MENU
								
							if prev != menu:
								print(" Menu = {}".format(menu))
												
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

							if hasTOF:
								# Read the Euler angles for heading, roll, pitch (all in degrees).
								heading, roll, pitch = bno.read_euler()
								distance = tof.get_distance()
								if distance > 0:
									print("%d mm, %d degrees" % (distance, heading))

							time.sleep(timing/1000000.00)
																					
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
			self.remote( joystick, gear )	
			return True
		if menu == 2:			
			self.straight( joystick, gear )
			return True
		if menu == 3:			
			self.mine( joystick, gear )
			return True
		if menu == 4:			
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
	def remote(self, joystick, gear):
		
		self.show("Remote mode")
					
		while True:		
			presses = joystick.check_presses()
			if presses.home:
				self.show('HOME pressed since last check')
				running = False
				break


			left_drive = joystick.ly
			right_drive = joystick.ry									
			self.bot.move(left_drive, right_drive, gear)

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
				
			if gear != prev:
				print(" Gear = {}".format(gear))
				
			self.bot.move(left_drive, right_drive, gear)			

	def maze(self, joystick):
		self.show("Escape Route mode")
		
	def mine(self, joystick, gear):
		self.show("Mine Sweeper mode")
		
		frameNo = 1.0;
		start = seconds()		
		
		#y_len = fwidth * fheight
		#uv_len = (fwidth // 2) * (fheight // 2)
		y_len = 32 * 32
		uv_len = (32 // 2) * (32 // 2)
		rawCapture = picamera.array.PiYUVArray( self.camera, size = (y_len + 2 * uv_len) )
		for frame in self.camera.CaptureContinous( rawCapture ):
			
			presses = joystick.check_presses()
			if presses.home:
				self.show('HOME pressed since last check')			
				running = False
				break
				
			image = frame.array			
			filename = "frame/frame{0:03.0f}.png".format(frameNo)
			self.writePNG(filename,image)
			frameNo += 1
			# minmax = self.camera.MinMaxRowwise(y_data)
			# y_data = self.camera.ExpandContrastRowwise( y_data, minmax )						
			# y_data = self.camera.Threshold(y_data, 200)
			# filename = "frame/frame{0:03.0f}.png".format(frame)
			# self.writePNG(filename,y_data)	
			# frame += 1
						
			#time.sleep(0.001)
	
		end = seconds()
		print("Frames: {0} in {1} seconds or {2} frames per second".format(frame, end-start, frame / (end-start)))

	def straight(self, joystick, gear):
		self.show("Lava Palava mode")
		
		frame = 1.0;
		start = seconds()		
		while True:
			
			presses = joystick.check_presses()
			if presses.home:
				self.show('HOME pressed since last check')			
				running = False
				break
				
			y_data = self.camera.GetYData();
			#self.writePNG("frame001.png",y_data)
			# Simulate white line on black background								
			y_data = self.camera.Invert( y_data )
			#self.writePNG("frame002.png",y_data)
			minmax = self.camera.MinMaxRowwise(y_data)
			y_data = self.camera.ExpandContrastRowwise( y_data, minmax )
			#self.writePNG("frame003.png",y_data)								
			y_data = self.camera.Threshold(y_data)
			#self.writePNG("frame004.png",y_data)
			y_data = self.camera.Slice(y_data)
			#self.writePNG("frame005.png",y_data)							
			# y_data, contours = self.camera.Contours(y_data)
			ydata, xTop  = self.camera.CentreTop(y_data, True)
			ydata, xBottom  = self.camera.CentreBottom(y_data, True)
			filename = "frame{0:03.0f}.png".format(frame)
			self.writePNG(filename,y_data)	
			frame += 1
			rate = self.camera.Rate(xTop,xBottom)
			self.bot.turn( rate, gear)                
			#time.sleep(0.001)
	
		end = seconds()
		print("Frames: {0} in {1} seconds or {2} frames per second".format(frame, end-start, frame / (end-start)))

	def showMenuImage(self, menu_img):
		cv.imshow('image',menu_img)
		cv.waitKey(10)
		
	def loadMenuImage(self, fileName):
		img = cv.imread(fileName,cv.IMREAD_COLOR)
		img = cv.resize(img,(1280,800), interpolation = cv.INTER_CUBIC)			
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
    # either fortronix, amybot or camjambot can be passed in, but only one
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument("--amybot", help="Use the kit amy has (whatever Jim provided)", action="store_true")
    # group.add_argument("--camjambot", help="Use the camjam edubot kit", action="store_true")    
    # group.add_argument("--fourtronix", help="Use the 4tronix controller", action="store_true")
    # parser.add_argument("--straight", help="go straight into straight line mode on start", action="store_true")
    args = parser.parse_args()

    controller = Controller()
    controller.run()
