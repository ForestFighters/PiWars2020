import time
import picamera
import picamera.array 
import numpy as np
import cv2 as cv


class Camera(object):
	
	def __init__(self, w = 32, h = 32 ):
		self.width = w
		self.height = h
		self.camera = picamera.PiCamera(
			resolution=(self.width, self.height),
			framerate=32,
			sensor_mode=5)
		
		# print(self.width, self.height)
		time.sleep(2)
		
	def CaptureContinous( self, rawCapture ):
		return self.camera.capture_continuous( rawCapture, format = "yuv", use_video_port = True)
	
		
	def GetBGRData(self):
		bgr_data = np.empty((self.height * self.width * 3), dtype=np.uint8)
		try:
			self.camera.capture(bgr_data, 'bgr')
		except IOError:
			pass
		
		bgr_data =bgr_data.reshape((self.height, self.width, 3))
		return bgr_data 
		
	def GetYData(self):
		y_data = np.empty((self.height, self.width), dtype=np.uint8)
		try:
			self.camera.capture(y_data, 'yuv', True, 0,False,)
		except IOError:
			pass
		y_data = y_data[:self.height, :self.width]
		# y_data now contains the Y-plane only
		return y_data

	
	def MinMaxRowwise(self, y_data):
		# print(self.width, self.height)	
		ret = np.empty((self.height, 2), dtype=np.uint8)
		for y in range(self.height):
			minimum = 255
			maximum = 0
			for x in range(self.width):
				# print(x,y)
				if y_data[ y, x ] < minimum:
					minimum = y_data[ y, x ]
				if y_data[ y, x ] > maximum:
					maximum = y_data[ y, x ]
							
			ret[y] = (maximum, minimum)
		
		return ret
		
	def Slice(self, y_data):			
		y_data = y_data[((self.height//2) - 5):((self.height//2) + 5), :self.width]
		return y_data	
		
	def Invert(self, y_data):
		for y in range(self.height):			
			for x in range(self.width):
				y_data[ y, x ] = 255 - y_data[ y, x ]				
		
		return y_data
		
		
	def Contours(self, y_data):
		y_data, contours, hierarchy = cv.findContours(y_data,cv.RETR_CCOMP,cv.CHAIN_APPROX_SIMPLE)
		y_data = cv.drawContours(y_data, contours, 1, (0,0,0), 3)	
		return y_data, contours
		
	def Centre(self, y_data, y, invert = False):
		if invert :
			black = 255
			white = 0
		else:
			black = 0
			white = 255
			
		start = 0
		end = 0
		startTemp = 0
		
		for x in range(self.width - 1):				
			# print(" X = {0}".format(x))
			# Leading edge or edge of field		
			if (y_data[ y, x ] == white and y_data[ y, x + 1 ] == black) or (y_data[ y, x] == black and startTemp == 0):
				startTemp = x
				#print("Start {}".format(startTemp))
			# Trailing edge
			if y_data[ y, x ] == black and y_data[ y, x + 1 ] == white :
				endTemp = x
				#print("End {}".format(endTemp))	
				if endTemp - startTemp > start - end:
					start = startTemp
					end = endTemp
		
		x = start + ((end - start)//2)
		#print("start={0}, end={1}, x={2}".format(start, end, x))
		return x
		
	def CentreTop(self, y_data, invert = False ):
		y = 0
		x = self.Centre(y_data, y, invert)
		y_data[ y, x] = 255 - y_data[ y, x]
		return y_data, x
		
	def CentreBottom(self, y_data, invert = False):
		y = 9
		x = self.Centre(y_data, y, invert)
		y_data[ y, x] = 255 - y_data[ y, x]
		return y_data, x
		
	#      Line
	# --- XXXXXXX -----------
	#            ^ middle
	#        ^ xTop
	#        
	# If diff > 0 then go right
	#
	#      Line
	# ----------- XXXXXXX ---
	#            ^ middle
	#                ^ xTop
	#
	# If diff < 0 then go left
	#        
	def Rate(self, xTop, xBottom):	
		middle = (self.width//2)	
		diff =  middle - xTop
		# print(" diff = {}".format(diff))
		return diff
			
			
			
	def Threshold(self, y_data, threshold = 170):	
		black = 0
		white = 255
		for y in range(self.height):			
			for x in range(self.width):				
				if y_data[ y, x ] > threshold:
					y_data[ y, x ] = white
				else:
					y_data[ y, x ] = black
		
		return y_data
					
	def ExpandContrastRowwise(self, y_data, minmax):	
		for y in range(self.height):	
			scale = 255.0 / ( 1.0 + minmax[ y, 0] - minmax[ y, 1] )
			for x in range(self.width):				
				y_data[ y, x ] = (y_data[ y, x ] - minmax[ y, 1]) * scale
				
		return y_data
