import gpiozero
import logging

from Adafruit_BNO055 import BNO055
import VL53L0X


LOGGER = logging.getLogger(__name__)

class Robot(object):
	"""self.bot
	Lowest possible abstraction of our robots.
	"""
	def __init__(self):
		#self.pan_servo = gpiozero.AngularServo(21)
		#self.tilt_servo = gpiozero.AngularServo(26)
		#self.right_motor = gpiozero.PhaseEnableMotor(9, 10)
		#self.left_motor = gpiozero.PhaseEnableMotor(22, 27) 
		self.second_servo = gpiozero.AngularServo(22)
		self.first_servo = gpiozero.AngularServo(12,min_angle=-90,max_angle=90)	
		self.fan_servo = gpiozero.AngularServo(20)
		self.fan_servo.angle = 90
		self.servo_off()
		self.first_angle = 0
		self.second_angle = 0
		
		M1DIR = 27
		M1PWM = 13
		M2DIR = 6
		M2PWM = 5
		# self.right_motor = gpiozero.PhaseEnableMotor(M1DIR, M1PWM)
		# self.left_motor = gpiozero.PhaseEnableMotor(M2DIR, M2PWM) 
		# self.right_motor.stop()		
		# self.left_motor.stop()
		self.right_pwm = gpiozero.PWMOutputDevice(M1PWM)
		self.right_dir = gpiozero.OutputDevice(M1DIR)
		self.left_pwm = gpiozero.PWMOutputDevice(M2PWM)
		self.left_dir = gpiozero.OutputDevice(M2DIR)
		
		try:	
			# Create a VL53L0X object
			self.tof = VL53L0X.VL53L0X()
			# Start ranging
			# tof.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
			self.tof.start_ranging(VL53L0X.VL53L0X_HIGH_SPEED_MODE)

			self.timing = self.tof.get_timing()
			if self.timing < 20000:
				self.timing = 20000
			print("Timing %d ms" % (self.timing/1000))
			
			self.hasTOF = True
		except:
			print("Problem init TOF")
			self.hasTOF = False

		# Raspberry Pi configuration with serial UART and RST connected to GPIO 18:
		self.bno = BNO055.BNO055(serial_port='/dev/serial0', rst=7)
		while True:
			try:
				self.bno.begin()
				break			
			except KeyboardInterrupt:
				# CTRL+C exit, disable all drives				
				return
			except:
				print("BNO Error")				
				#raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')
				
		# Print BNO055 software revision and other diagnostic data.
		sw, bl, accel, mag, gyro = self.bno.get_revision()
		print('Software version:   {0}'.format(sw))
		print('Bootloader version: {0}'.format(bl))
		print('Accelerometer ID:   0x{0:02X}'.format(accel))
		print('Magnetometer ID:    0x{0:02X}'.format(mag))
		print('Gyroscope ID:       0x{0:02X}\n'.format(gyro))
		
	def readEuler( self ):
		return self.bno.read_euler()
	
	def getInterval( self ):
		return (self.timing/1000000.00)
		
	def getDistance( self ):
		return self.tof.get_distance()
			
	def turnTo( self, angle, heading ):		
		self.stop()
		
		# Map anything greater than 270 as 0
		if heading > 270:
			heading = 0
			
		if angle > heading:			
			while True:
				# turnClockwise
				heading, roll, pitch = self.readEuler()				
				if heading > 270:
					heading = angle
				print("Target = %d Degrees = %d" % (angle, heading))				
				if heading >= angle:
					break
				left_drive = 1
				right_drive = -1
				self.move(left_drive, right_drive, 1)
		else:			
			while True:
				# turnAntiClockwise
				heading, roll, pitch = self.readEuler()
				print("Target = %d Degrees = %d" % (angle, heading))
				if heading <= angle:
					break
				left_drive = -1
				right_drive = 1
				self.move(left_drive, right_drive, 1)
		
		self.stop()
		
		
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
			# self.left_motor.forward(left_drive)			
			self.left_pwm.value = left_drive
			self.left_dir.off()
		elif left_drive < 0:
			self.left_pwm.value = abs(left_drive)
			self.left_dir.on()
		else:
			self.left_pwm.value = 0.0
			self.left_dir.toggle()
				
		if right_drive > 0:
			# self.right_motor.forward(right_drive)
			self.right_pwm.value = right_drive
			self.right_dir.off()
		elif right_drive < 0:
			# self.right_motor.backward(-right_drive)
			self.right_pwm.value = abs(right_drive)
			self.right_dir.on()
		else:
			# self.right_motor.stop()
			self.right_pwm.value = 0.0
			self.right_dir.toggle()
	
	def pan(self, amount):
		angle = self.second_servo.angle
		if angle == None:
			angle = self.second_angle		
		angle = angle + amount
		if angle >= -90 and angle <= 90:                   
			self.second_servo.angle = angle			
			self.second_angle = angle
			print(angle)    
		
	def tilt(self, amount):
		angle = self.first_servo.angle		
		if angle == None:
			angle = self.first_angle
		angle = angle + amount
		if angle >= -90 and angle <= 90: 
			print(angle)                  
			self.first_servo.angle = angle	
			self.first_angle = angle
								
	def trigger(self, angle):		
		if angle >= -90 and angle <= 90:                   
			print(angle)
			self.first_servo.angle = angle
			self.first_angle = angle			
			
	def servo_off(self):
		self.second_servo.value = None
		self.first_servo.value = None		

	def stop(self):
		# self.left_motor.stop()
		# self.right_motor.stop()
		self.right_pwm.value = 0.0
		self.left_pwm.value = 0.0
		self.right_dir.toggle()		
		self.left_dir.toggle()
