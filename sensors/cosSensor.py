"""Testing class for sensor output"""

import math

class cosSensor:
    sensorNum = 0

    def __init__(self):

        # Important constants
        self.maxReadFrequency = 20 # Hz
        self.name = "cos"

        self.time = 0. # Counter for sin
        # Connect/intialize with a sensor
    
    def initInProcess(self):
        """Run initialization commands when this sensor is accessed by the data collection process"""
        pass

    def reset(self):
        """The reset function sets the sensor number for the entire class to 0. This is necessary to make
        the flashdrive "plug and play" while supporting multiple sensors of the same type that have different
        pin assignments."""
        self.__class__.sensorNum = 0

    def read(self):
        
        val = math.cos(self.time)
        self.time += 0.2
        return val
    
    def convert(self, val):
        return val * 13
