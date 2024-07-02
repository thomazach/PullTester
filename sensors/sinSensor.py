"""Testing class for sensor output"""

import math

class sinSensor:

    def __init__(self):

        # Important constants
        self.maxReadFrequency = 20 # Hz
        self.name = "sin" # For testing only

        self.time = 0. # Counter for sin

        # Connect/intialize with a sensor
    
    def read(self): 

        val = math.sin(self.time)
        self.time += 0.2
        return val
    
    def convert(self, val):
        return val * 10

    def calibrate(self):
        pass
