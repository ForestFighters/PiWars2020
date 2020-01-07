import gpiozero
import logging


LOGGER = logging.getLogger(__name__)

class Robot(object):
	"""
	Lowest possible abstraction of our robots.
	"""
	def __init__(self):
		#self.pan_servo = gpiozero.AngularServo(21)
		#self.tilt_servo = gpiozero.AngularServo(26)
		#self.right_motor = gpiozero.PhaseEnableMotor(9, 10)
		#self.left_motor = gpiozero.PhaseEnableMotor(22, 27) 
		self.pan_servo = gpiozero.AngularServo(22)
		self.tilt_servo = gpiozero.AngularServo(12)
		self.right_motor = gpiozero.PhaseEnableMotor(6, 5)
		self.left_motor = gpiozero.PhaseEnableMotor(27, 13) 
		self.right_motor.stop()		
		self.left_motor.stop()
		
	def turn(self, diff, gear):
		
		left_drive = 1.0
		right_drive = 1.0
		
		# dead zone between -4 and +4
		#  
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
		
		if( diff > 4 ):
			right_drive = right_drive - (diff / 100.0)
		
		if( diff < -4 ):
			left_drive = left_drive + (diff / 100.0)
		
		self.move( left_drive, right_drive, gear)
			

	def move(self, left_drive, right_drive, gear):
		
		if (left_drive != 0 or right_drive != 0):
			LOGGER.debug("left_drive: {}; right_drive: {}; gear: {} ".format(left_drive, right_drive, gear ))
		
		if (left_drive < 0 and right_drive > 0) or (left_drive > 0 and right_drive < 0):			
			gear = 1;
									 
		left_drive = left_drive / gear
		right_drive = right_drive / gear
												
		if left_drive > 0:
			self.left_motor.forward(left_drive)
		elif left_drive < 0:
			self.left_motor.backward(-left_drive)
		else:
			self.left_motor.stop()
				
		if right_drive > 0:
			self.right_motor.forward(right_drive)
		elif right_drive < 0:
			self.right_motor.backward(-right_drive)
		else:
			self.right_motor.stop()
	
	def pan(self, amount):
		angle = self.pan_servo.angle
		if angle == None:
			angle = 0;
		angle = angle + amount
		if angle >= -90 and angle <= 90:                   
			self.pan_servo.angle = angle
			print(angle)    
		
	def tilt(self, amount):
		angle = self.tilt_servo.angle
		if angle == None:
			angle = 0;
		angle = angle + amount
		if angle >= -90 and angle <= 90:                   
			self.tilt_servo.angle = angle
			print(angle)    
	
	def servo_off(self):
		self.pan_servo.angle = None
		self.tilt_servo.angle = None

	def stop(self):
		self.left_motor.stop()
		self.right_motor.stop()
