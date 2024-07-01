""" Program start point, work in progress """
import os
import sys
import csv
import time
import yaml

from multiprocessing import Process, Queue, Pipe

# Add base directory to system path for importing
thisDir = os.path.dirname(__file__)
baseDir = thisDir[0:thisDir.find("PullTester") + 10]
sys.path.append(baseDir)
os.chdir(baseDir)

from sensors.sinSensor import sinSensor
from sensors.cosSensor import cosSensor
from src.gui import GUI

### Data collection functions ###
def sensorWrapper(sensors, dataQueue, commandPipe):
    """This function facilitates the reading of sensors when requested. Its been seperated from the
    read() method of each unique sensor class to reduce repeated code and make the creation of new 
    custom sensors easier.
    
    Input:
        sensors: 
            A list where each element is an object representing a sensor with the required constants and
            read() method (see sensors/Custom Sensor Format/SensorNameHere.py)
        dataQueue:
            The multiprocessing.Queue assigned to store this sensors data
        commandPipe:
            Pipe used to recieve collect, stop, and shutdown commands
    
    Output:
        val: int, or float
            Raw sensor value, val is not directly returned, but instead put into the dataQueue
            
    """

    # Find lowest read speed
    maxReadFrequency = []
    for sensor in sensors:
        maxReadFrequency += [sensor.maxReadFrequency]
    maxReadFrequency = min(maxReadFrequency)

    # Setup logic for this process and start listening for commands
    shutDown = False
    beginRead = False
    newCmd = None
    while not shutDown:

        if commandPipe.poll():
            newCmd = commandPipe.recv()

        match newCmd:

            case "read":
                startTime = time.time()
                beginRead = True

            case "stop":
                beginRead = False

            case "off":
                shutDown = True
                break
        newCmd = None # Makes each of these cases run once uppon recieving a new command

        if beginRead:
            data = [time.time() - startTime]
            for sensor in sensors:
                data += [sensor.read()]

            dataQueue.put(data)
            time.sleep(1 / maxReadFrequency)
            continue

        time.sleep(0.1) # Check if we should be reading sensors every tenth of a second

def queueReader(dataQueue):
    """Reads from a queue and centralizes the information into a multi dimensional array.
    Input:
        dataQueue: 
            multiprocessing.Queue that may or may not contain data from the sensors
    
    Output:"""

    queueData = []
    while not dataQueue.empty(): # TODO: Figure out if this will hang if reading a high Hz sensor
        vals = dataQueue.get()
        queueData += [vals]

    if queueData == []:
        return None

    return queueData
           
def pipeMessager(pipes, command):
    """ Send the same command to several different pipes. """

    for pipe in pipes:
        pipe.send(command)

### Matplotlib formal graphing functions ###

### CSV and data sharing functions ### 
def writeCSV(data, runNumber, sensorNames):

    with open(str(runNumber) + '.csv', 'w', newline='') as f:
        writer = csv.writer()
        writer.writerows(data)  

def main():

    """Dev thing to correctly format yaml file with new test variables"""
    settingsDict = {'selectedSensors': ["cosSensor", "sinSensor"],
     'convert': False,
     'sampleRate': 10,
     'columnNames': ["Cos", "Sin"]
    }
    
    with open("config.yaml", "w") as f:
        yaml.dump(settingsDict, f)
    
    return


    ### Load from config file
    with open("config.yaml", "r") as f:
        settingsDict = yaml.safe_load(f)

    print(settingsDict)
    return
    
    ### Create GUI
    guiQueue = Queue()
    guiParent, guiChild = Pipe()
    terminalGUI = GUI(guiChild, guiQueue)
    Process(target=terminalGUI.mainLoop).start()

    # TODO: Implement sensor selection, for now, it will be a list
    selectedSensors = [sinSensor(), cosSensor()] # Note that the mere call to the class connects each sensor
    # TODO: Implement mode selection

    sensorQueue = Queue()
    parentPipe, childPipe = Pipe()
    parentCommandPipes = [parentPipe]
    Process(target=sensorWrapper, args=(selectedSensors, sensorQueue, childPipe)).start()


    while True:
        response = input("Run (y/n)") # TODO: Placeholder for physical button on device
        if response.lower() == "y":
            break
    
    pipeMessager(parentCommandPipes + [guiParent], "read")

    time.sleep(0.1)

    data = queueReader(sensorQueue)

    while True:

        newData = queueReader(sensorQueue)

        if newData != None:
            data += newData
            guiQueue.put(data)
  
if __name__ == "__main__":
    main()