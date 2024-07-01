"""
Example file format to be used for custom sensors. This sensor object will be referenced by its file name (which should match the class name of the sensor). It needs to
include relevant sensor information attributes as well as a read() method
"""

class SensorNameHere:

    def __init__(self):
        """ Run once when adding a sensor. After running __init__, your sensor should be ready to have read() called and return data"""

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

