import RPi.GPIO as GPIO
from hx711 import HX711

class hx711LoadCell:
    sensorNum = 0
    sensorPins = [[24, 23]]

    calibrationRatios = [1] # Calibration for each hx711 load cell amplifier, assigned by ID.

    def __init__(self):
        """ Run once when adding a sensor. After running __init__, your sensor should be ready to have read() called and return data"""
        # Assign sensor ID
        self.ID = hx711LoadCell.sensorNum
        hx711LoadCell.sensorNum += 1

        # Important constants
        self.maxReadFrequency = 100 # Hz
        self.conversionRatio = hx711LoadCell.calibrationRatios[self.ID]
        self.name = "hx711LoadCell"
        self.hasRead = False

        # Organize pin numbers
        self.dataPin, self.clockPin = hx711LoadCell.sensorPins[self.ID]
        
        # Connect/intialize with a sensor

    def initInProcess(self):
        # Assign pins, must be done when run by data collection process since 
        # gpio pins must be in the same process OR scope
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.hx = HX711(dout_pin=self.dataPin, pd_sck_pin=self.clockPin) # Note that this class handles gpio pin setup as IN/OUT


    def read(self):
        "Read raw data from the sensor"

        val = self.hx.get_raw_data_mean(readings=1)

        if val == -1:
            return float("nan")
        
        return val

    def convert(self, value):
        "Convert the raw value to the desired display value."
        data = value / self.conversionRatio
        return data


