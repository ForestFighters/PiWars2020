import time
import picamera
import picamera.array
import numpy as np


class Camera(object):
	
	def __init__(self):
		self.camera = picamera.PiCamera(
			resolution=(32, 32),
			framerate=60,
			sensor_mode=5)
		
		time.sleep(2)
		
	def GetYData(self):
		y_data = np.empty((32, 32), dtype=np.uint8)
		try:
			self.camera.capture(y_data, 'yuv', True, 0,False,)
		except IOError:
			pass
		y_data = y_data[:32, :32]
		# y_data now contains the Y-plane only
		return y_data

	
	def MinMaxRowwise(self, y_data):	
		ret = np.empty((32,2), dtype=np.uint8)
		for y in range(32):
			minimum = 255
			maximum = 0
			for x in range(32):
				if y_data[ x, y ] < minimum:
					minimum = y_data[ x, y ]
				if y_data[ x, y ] > maximum:
					maximum = y_data[ x, y ]
			
			ret[y] = (maximum, minimum)
		
		return ret
					
	def Threshold(self, y_data):	
		for y in range(32):			
			for x in range(32):
				if y_data[ x, y ] > 130:
					y_data[ x, y ] = 255
				else:
					y_data[ x, y ] = 0
		
		return y_data
					
	def ExpandContrastRowwise(self, y_data, minmax):	
		for y in range(32):	
			scale = 255.0 / ( 1.0 + minmax[ y, 0] - minmax[ y, 1] )
			for x in range(32):				
				y_data[ x, y ] = (y_data[ x, y ] - minmax[ y, 1]) * scale
				
		return y_data
