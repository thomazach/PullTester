"""Testing class for sensor output"""

import math

class cosSensor:

    def __init__(self):

        # Important constants
        self.maxReadFrequency = 20 # Hz
        self.name = "cos"

        self.time = 0. # Counter for sin
        # Connect/intialize with a sensor
    
    def initInProcess(self):
        """Run initialization commands when this sensor is accessed by the data collection process"""
        pass

    def read(self):
        
        val = math.cos(self.time)
        self.time += 0.2
        return val
    
    def convert(self, val):
        return val * 13
