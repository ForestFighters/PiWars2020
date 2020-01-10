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
from time import sleep

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
			hasCamera = True
		except:
			hasCamera = False
		
		interval = 0.0
				
		super().__init__()

	def run(self):  
		self.show('Started')					
		gear = 2
		running = True
		while running:	  
			try:
				self.show('Press CTRL+C to quit')
				with ControllerResource() as joystick: 
					if joystick.connected :					
						# Loop indefinitely
						while running:
							presses = joystick.check_presses()
							if presses.home:
								self.show('HOME pressed since last check')
								running = False
								break
							
							if presses.square:
								self.show('Y pressed since last check')
								self.bot.servo_off()
								self.straight( joystick, gear )
								
							if presses.circle:
								self.show('A pressed since last check')
								self.bot.servo_off()
								self.mine( joystick, gear )
									
							left_drive = joystick.ly
							right_drive = joystick.ry									
							self.bot.move(left_drive, right_drive, gear)
														
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
									
							if joystick.presses.dup:
								self.bot.tilt( -10 )                   
							if joystick.presses.ddown:
								self.bot.tilt( 10 )

							if joystick.presses.dright:
								self.bot.pan( -5 )                   
							if joystick.presses.dleft:
								self.bot.pan( 5 )
																							
							# Select menu option                    
							# time.sleep(INTERVAL)
			
			except IOError:
					LOGGER.info('Unable to find joystick')
					time.sleep(4.0)
					
			except KeyboardInterrupt:
				# CTRL+C exit, disable all drives
				self.bot.move(0, 0)
				self.show('Motors off')
				break

	# Pi Noon, Zombie Shoot, Temple of Doom, Eco Disaster
	def remote(self, left_drive, right_drive, gear):
		self.show("Remote mode")		
		self.bot.move(left_drive, right_drive, gear)

	def maze(self):
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
