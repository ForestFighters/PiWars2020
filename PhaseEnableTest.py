#!/usr/bin/python
from approxeng.input.selectbinder import ControllerResource
import gpiozero
import time
import VL53L0X

tof = VL53L0X.VL53L0X()
tof.start_ranging(1) # Start ranging, 1 = Short Range, 2 = Medium Range, 3 = Long Range

#right_motor = gpiozero.PhaseEnableMotor(13, 6)
#left_motor = gpiozero.PhaseEnableMotor(26, 19)

right_motor = gpiozero.PhaseEnableMotor(9, 10)
left_motor = gpiozero.PhaseEnableMotor(22, 27) 

panangle = 0
tiltangle = 0

pan_servo = gpiozero.AngularServo(21)
tilt_servo = gpiozero.AngularServo(26)

pan_servo.angle = panangle
tilt_servo.angle = tiltangle
#pantilthat.pan(panangle)
#pantilthat.tilt(tiltangle)

running = True
while running:
    try:
        # Get a joystick
        with ControllerResource() as joystick:      
            # Loop until we're disconnected 
            while joystick.connected:
                # Check joystick 
                presses = joystick.check_presses()
                if joystick.presses.home:
                    print('HOME pressed since last check')
                    running = False
                    break
                    
                if joystick.presses.dup:
                    tiltangle -= 10
                    if tiltangle <= -90:
                        tiltangle = -90
                    tilt_servo.angle = tiltangle
                    print(tiltangle)    
                if joystick.presses.ddown:
                    tiltangle += 10
                    if tiltangle >= 90:
                        tiltangle = 90
                    tilt_servo.angle = tiltangle
                    print(tiltangle)    
                
                if joystick.presses.dleft:
                    panangle += 5
                    if panangle >= 90:
                            panangle = 90
                    pan_servo.angle = panangle
                    print(panangle)     
                if joystick.presses.dright:
                    panangle -= 5
                    if panangle <= -90:
                        panangle = -90
                    pan_servo.angle = panangle
                    print(panangle)     
                                        
                distance_in_mm = tof.get_distance() # Grab the range in mm
                print("Distance = ", distance_in_mm)
                left_y = joystick.ly
                right_y = joystick.ry
                            
                left_speed = abs(left_y)
                right_speed = abs(right_y)
                
                if (left_y > 0) and (right_y > 0):
                    left_motor.forward(left_speed)
                    right_motor.forward(right_speed)
                elif (left_y < 0) and (right_y < 0):
                    left_motor.backward(left_speed)
                    right_motor.backward(right_speed)
                elif (left_y > 0) or (right_y < 0):        
                    left_motor.forward(left_speed)
                    right_motor.backward(right_speed)
                elif (left_y < 0) or (right_y > 0):        
                    left_motor.backward(left_speed)
                    right_motor.forward(right_speed)
                else :
                    left_motor.stop()
                    right_motor.stop()
                    
                if pan_servo.angle == 0:
                    pan_servo.angle = None
                    
                if tilt_servo.angle == 0:
                    tilt_servo.angle = None
                                    
                    
                time.sleep(0.1)
                
    except IOError:
        print("Unable to find joystick")
        time.sleep(4.0)
        
left_motor.stop()
right_motor.stop()
tof.stop_ranging() # Stop ranging
