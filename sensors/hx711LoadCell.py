import RPi.GPIO as GPIO
from hx711 import HX711

class hx711LoadCell:
    sensorNum = 0
    sensorPins = [[24, 23]]

    def __init__(self):
        """ Run once when adding a sensor. After running __init__, your sensor should be ready to have read() called and return data"""
        # Assign sensor ID
        self.ID = hx711LoadCell.sensorNum
        hx711LoadCell.sensorNum += 1

        # Important constants
        self.maxReadFrequency = 80 # Hz
        self.name = "hx711LoadCell"

        # Organize pin numbers
        self.dataPin, self.clockPin = hx711LoadCell.sensorPins[self.ID]

        # Control logic
        self.previousVal = None
        self.filterData = True
        self.recentData = []
        
        # Connect/intialize with a sensor

    def initInProcess(self):
        # Assign pins, must be done when run by data collection process since 
        # gpio pins must be in the same process OR scope
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.hx = HX711(dout_pin=self.dataPin, pd_sck_pin=self.clockPin) # Note that this class handles gpio pin setup as IN/OUT

    def reset(self):
        """The reset function sets the sensor number for the entire class to 0. This is necessary to make
        the flashdrive "plug and play" while supporting multiple sensors of the same type that have different
        pin assignments."""
        self.__class__.sensorNum = 0

    def read(self):
        "Read raw data from the sensor"

        val = self.hx._read()

        if val == -1:
            return float("nan")
        else:
            self.recentData += [val]
        
        # Filter sensor noise
        if len(self.recentData) == 3: # Sensor is in steady state
            # If the sensor has output a ridiculous value in between two similar values
            if abs(self.recentData[0] - self.recentData[1]) > 300000 and abs(self.recentData[1] - self.recentData[2]) > 300000:# and abs(self.recentData[0] - self.recentData[2]) < 1000000:
                # if middle value is a large change relative to the first, and if the middle value is a large change realtive to the third, and the first and third data points are similar
                self.recentData[1] = (self.recentData[0] + self.recentData[2])/2 # Make the bad data the mean of the surrounding points

            # Low pass extreme changes to lessen the impact of sensor noise not caught by the above filter
            elif abs(self.recentData[0] - self.recentData[1]) > 500000:
                self.recentData[1] = self.recentData[0] + 0.05 * (self.recentData[1] - self.recentData[0])
            
            val = self.recentData[0]
            self.recentData.pop(0)
    
        return val

    def convert(self, value):
        "Convert the raw value to the desired display value."

        ### Calibration Points ### 
        # 200lbs = 618750 = 90.7185 kg
        # 50lbs = 167010 = 22.6796 kg
        m = 0.0001506151769 # (90.7185 - 22.6796)/(618750 - 167010)
        b = -2.474640689
        data = value * m + b
        return data


