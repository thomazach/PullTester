"""Testing class for sensor output"""

import math

class cosSensor:

    def __init__(self):

        # Important constants
        self.maxReadFrequency = 20 # Hz
        self.type = "cos" # For testing only

        self.time = 0. # Counter for sin
        # Connect/intialize with a sensor
    

    def read(self):
        
        val = math.cos(self.time)
        self.time += 0.2
        return val
