"""
Example file format to be used for custom sensors. This sensor object will be referenced by its file name (which should match the class name of the sensor). It needs to
include relevant sensor information attributes as well as a read() method
"""

class SensorNameHere:
    sensorNum = 0
    sensorPins = [[1, 4], # Each row represents an additional sensor of the same type,
                  [2, 5,], # the numbers correspond to pins on the raspi which should be
                  [3, 6]]  # referenced in the read function

    def __init__(self):
        """ Run once when adding a sensor. After running __init__, your sensor should be ready to have read() called and return data"""
        # Handle the case where there are multiple sensors of the same type
        # attached to different pins
        self.ID = SensorNameHere.sensorNum
        SensorNameHere.sensorNum += 1

        # Important constants
        self.name = "SensorNameHere"
        self.maxReadFrequency = 100 # Hz
        
        # Connect/intialize with a sensor
    
    def read(self):
        "Read data from the sensor"
        pass

    def convert(self, value):
        "Convert the raw value to the desired display value."
        pass

