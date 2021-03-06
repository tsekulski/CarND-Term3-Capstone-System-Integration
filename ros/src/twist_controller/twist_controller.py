from yaw_controller import YawController
from pid import PID
from lowpass import LowPassFilter
import rospy
import random

GAS_DENSITY = 2.858
ONE_MPH = 0.44704
DEBUGGING = False

class Controller(object):
    def __init__(self, *args, **kwargs):
        # TODO: Implement
        self.vehicle_mass = args[0]
        self.fuel_capacity = args[1]
        self.brake_deadband = args[2]
       	self.decel_limit = args[3]
        self.accel_limit = args[4]
        self.wheel_radius = args[5]
        self.wheel_base = args[6]
        self.steer_ratio = args[7]
        self.max_lat_accel = args[8]
        self.max_steer_angle = args[9]

        # Define minimum speed for the YawController - my understanding is that this is simply to ensure that the car is not steering when it's not moving
        self.min_speed = 0. # m/s


        # Createa a YawController object - to be used to generate steering values
        self.yaw_controller = YawController(self.wheel_base, self.steer_ratio, self.min_speed, self.max_lat_accel, self.max_steer_angle)

        # Create a LowPassFilter object - to smoothen steering angles
        self.lowpass_steer = LowPassFilter(1, 1)
        self.lowpass_throttle = LowPassFilter(1, 1)

        # Create a PID controller for throttle
        self.pid_filter = PID(kp=2.0, ki=0.4, kd=0.1, mn=self.decel_limit, mx=self.accel_limit)


        if DEBUGGING:
            rospy.logwarn("Controller object initialized")

    def control(self, *args, **kwargs):
        # TODO: Change the arg, kwarg list to suit your needs
        # Return throttle, brake, steer

        target_linear_velocity = args[0]
        target_angular_velocity = args[1]
        current_linear_velocity = args[2]
        current_angular_velocity = args[3]
        dbw_enabled = args[4]
        time_diff = args[5]

        if not dbw_enabled:
        	self.pid_filter.reset()
        	#rospy.logwarn("Manual control!")

        # Get steering angle
        steer = self.yaw_controller.get_steering(target_linear_velocity, target_angular_velocity, current_linear_velocity)

        # Smoothen steering angle
        steer = self.lowpass_steer.filt(steer)

        # Note to self: implement also controllers for throttle and brake
        #steer = -5.0
        #throttle = 0.07 + random.randint(1,5) / 100.0
        error = target_linear_velocity - current_linear_velocity
        acceleration = self.pid_filter.step(error, time_diff)
        acceleration = self.lowpass_throttle.filt(acceleration)

        if acceleration > 0.0:
            throttle = acceleration
            brake = 0.0
        else:
            throttle = 0.0
            if acceleration > self.brake_deadband:
                brake = 0.0
            else:
            	brake = (-1) * (self.vehicle_mass + self.fuel_capacity * GAS_DENSITY) * acceleration * self.wheel_radius

        #if (target_linear_velocity < 0.1):
        #	throttle = 0.0
        #	brake = 1.0

        	'''
        	if (throttle > 0):
        		brake = 0
        	else:
        		decceleration = throttle * (-1)
        		throttle = 0
        		if (decceleration < self.brake_deadband):
        			decceleration = 0
        		brake = decceleration * (self.vehicle_mass + self.fuel_capacity * GAS_DENSITY) * self.wheel_radius

        	# Make sure that the car comes to a full stop when needed
        	if (target_linear_velocity == 0) and (current_linear_velocity - target_linear_velocity < 0.3):
        		throttle = 0.0
        		brake = 1.0
        	'''

        if DEBUGGING:
            #rospy.logwarn("Control values returned")
            rospy.logwarn("steer %s", steer)
            rospy.logwarn("throttle %s", throttle)
            rospy.logwarn("brake %s", brake)

        return throttle, brake, steer
