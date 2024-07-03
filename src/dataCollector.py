import time

class dataCollector:
    """This class facilitates the reading of sensors when requested. Its been seperated from the
    read() method of each unique sensor class to reduce repeated code and make the creation of new 
    custom sensors easier.
    
    Generalized Input:
        sensors: 
            A list where each element is an object representing a sensor with the required constants and
            read() method (see sensors/Custom Sensor Format/SensorNameHere.py)
        dataQueue:
            The multiprocessing.Queue assigned to store sensor data
        commandPipe:
            Pipe used to recieve collect, stop, and shutdown commands
    
    Generalized Output:
        val: int, or float
            Raw sensor value, val is not directly returned, but instead put into the dataQueue
            
    """

    def __init__(self, sensors, dataQueue, commandPipe, settingsDict):

        self.sensors = sensors
        self.dataQueue = dataQueue
        self.commandPipe = commandPipe
        self.settingsDict = settingsDict

        # Get the sample rate, if none is provided use the slowest sensor as the maximum sample rate
        if settingsDict['sampleRate'] == None:
            maxReadFrequency = []
            for sensor in sensors:
                maxReadFrequency += [sensor.maxReadFrequency]
            maxReadFrequency = min(maxReadFrequency)
        else:
            if isinstance(settingsDict['sampleRate'], (float, int)):
                maxReadFrequency = settingsDict['sampleRate']
            else:
                print(f"ERROR: Bad sampleRate value in config.yaml, must be of type int or float.")
        self.maxReadFrequency = maxReadFrequency

        # Control variables for the main loop
        self.shutDown = False
        self.beginRead = False
        self.newCmd = None

    def setSettingsDict(self, settingsDict):
        """Setter method for settings dictionary. Used to update the settings used to collect
        data.
        NOTE: This is only safe to use when the system is not collecting data, and this class
         is not responsible for formatting column names/table data."""
        self.settingsDict = settingsDict

    def setSensors(self, sensors):
        """Setter method for sensor object. Used to update the selected sensors
        after intializing the GUI. 
        NOTE: This is only safe to use when the system is not collecting data. """
        self.sensors = sensors

    def mainLoop(self):

        while not self.shutDown:

            if self.commandPipe.poll():
                self.newCmd = self.commandPipe.recv()

            # Use if instead of match due to python 3.9.2
            if self.newCmd == "read":
                startTime = time.time()
                self.beginRead = True

            if self.newCmd == "stop":
                self.beginRead = False

            if self.newCmd == "off":
                self.shutDown = True
                break

            if self.newCmd == "set sensors":
                self.setSensors(self.commandPipe.recv())
            
            if self.newCmd == "set settings":
                self.setSettingsDict(self.commandPipe.recv())

            self.newCmd = None # Makes each of these cases run once uppon recieving a new command

            if self.beginRead:
                data = [time.time() - startTime]
                for sensor in self.sensors:
                    val = None
                    # Convert if requested, default to storing raw values
                    if self.settingsDict['convert'] == True:
                        data += [sensor.convert(sensor.read())]
                    else:
                        data += [sensor.read()]

                self.dataQueue.put(data)
                time.sleep(1 / self.maxReadFrequency)
                continue

            time.sleep(0.1) # Check if we should be reading sensors every tenth of a second
