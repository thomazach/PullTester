""" Program start point, work in progress """
import os
import sys
import csv
import time
import yaml
import threading
import glob

from multiprocessing import Process, Queue, Pipe
from datetime import datetime, timedelta

import seeed_python_reterminal.core as rt
import seeed_python_reterminal.button as rtButton

# Add base directory to system path for importing
thisDir = os.path.dirname(__file__)
baseDir = thisDir[0:thisDir.find("PullTester") + 10]
sys.path.append(baseDir)
os.chdir(baseDir)

### Sensor Imports ###
from sensors.sinSensor import sinSensor
from sensors.cosSensor import cosSensor

### Core Component Imports ###
from src.gui import GUI
from src.dataCollector import dataCollector

# ### Data collection functions ###
# def sensorWrapper(sensors, dataQueue, commandPipe, settingsDict):
#     """This function facilitates the reading of sensors when requested. Its been seperated from the
#     read() method of each unique sensor class to reduce repeated code and make the creation of new 
#     custom sensors easier.
    
#     Input:
#         sensors: 
#             A list where each element is an object representing a sensor with the required constants and
#             read() method (see sensors/Custom Sensor Format/SensorNameHere.py)
#         dataQueue:
#             The multiprocessing.Queue assigned to store this sensors data
#         commandPipe:
#             Pipe used to recieve collect, stop, and shutdown commands
    
#     Output:
#         val: int, or float
#             Raw sensor value, val is not directly returned, but instead put into the dataQueue
            
#     """

#     # Find lowest read speed
#     if settingsDict['sampleRate'] == None:
#         maxReadFrequency = []
#         for sensor in sensors:
#             maxReadFrequency += [sensor.maxReadFrequency]
#         maxReadFrequency = min(maxReadFrequency)
#     else:
#         if isinstance(settingsDict['sampleRate'], (float, int)):
#             maxReadFrequency = settingsDict['sampleRate']
#         else:
#             print(f"ERROR: Bad sampleRate value in config.yaml, must be of type int or float.")

#     # Setup logic for this process and start listening for commands
#     shutDown = False
#     beginRead = False
#     newCmd = None
#     while not shutDown:

#         if commandPipe.poll():
#             newCmd = commandPipe.recv()

#         # Use if instead of match due to python 3.9.2

#         if newCmd == "read":
#             startTime = time.time()
#             beginRead = True

#         if newCmd == "stop":
#             beginRead = False

#         if newCmd == "off":
#             shutDown = True
#             break
#         newCmd = None # Makes each of these cases run once uppon recieving a new command

#         if beginRead:
#             data = [time.time() - startTime]
#             for sensor in sensors:
#                 val = None
#                 # Convert if requested, default to storing raw values
#                 if settingsDict['convert'] == True:
#                     data += [sensor.convert(sensor.read())]
#                 else:
#                     data += [sensor.read()]

#             dataQueue.put(data)
#             time.sleep(1 / maxReadFrequency)
#             continue

#         time.sleep(0.1) # Check if we should be reading sensors every tenth of a second

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
def writeCSV(data, runNumber, settingsDict, path=None):

    if path == None:
        path = baseDir

    # Get useful time strings
    now = datetime.now()
    day = now.strftime("%m-%d-%Y")
    hour = now.strftime("%I_%M_%p")

    
    os.system(f"mkdir -p {path}/Data/{day} && touch {path}/Data/{day}/Run{runNumber}_{hour}.csv")
    with open(f"{path}/Data/{day}/Run{runNumber}_{hour}.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time (seconds)"] + settingsDict['columnNames'])
        writer.writerows(data)  

def reterminalControls(buttonDevice):
    global doCollect

    timeout = 0.5
    previousPress = time.time()
    ### Controls
    for event in buttonDevice.read_loop():
        buttonEvent = rtButton.ButtonEvent(event)
        if buttonEvent.name != None and (time.time() > previousPress + timeout):
            previousPress = time.time()
            if str(buttonEvent.name) == "ButtonName.O":
                doCollect = not doCollect # Toggle doCollect between true and false

# Global scope variable used for terminal control
doCollect = False
def main():

    # """Dev thing to correctly format yaml file with new test variables"""
    # settingsDict = {'selectedSensors': ["cosSensor", "sinSensor"],
    #  'convert': False,
    #  'sampleRate': None,
    #  'columnNames': ["Cos", "Sin"]
    # }
    
    # with open("config.yaml", "w") as f:
    #     yaml.dump(settingsDict, f)
    
    # return

    ### Load settings from default config file ###
    with open("config.yaml", "r") as f:
        settingsDict = yaml.safe_load(f)

    selectedSensors =[]
    for className in settingsDict['selectedSensors']:
        
        if className == "sinSensor":
            selectedSensors += [sinSensor()]
        
        if className == "cosSensor":
            selectedSensors += [cosSensor()]
    
    ### Create GUI process ###
    guiQueue = Queue()
    guiParent, guiChild = Pipe()
    terminalGUI = GUI(guiChild, guiQueue, selectedSensors)
    Process(target=terminalGUI.mainLoop).start()

    ### Create sensor process ###
    sensorQueue = Queue()
    parentPipe, childPipe = Pipe()
    sensorReader = dataCollector(selectedSensors, sensorQueue, childPipe, settingsDict)
    Process(target=sensorReader.mainLoop).start()

    ### Create control input thread for the reterminal ###
    reterminalButtonDevice = rt.get_button_device()
    reterminalThread = threading.Thread(target=reterminalControls, args=(reterminalButtonDevice,))
    reterminalThread.start()

    # Control logic
    global doCollect
    firstCollection = True
    connected = False # Flash drive

    # Counters
    runNumber = 0
    
    while True:

        ### Flash drive detection ###
        if not doCollect: # Do only when not collecting because updating settings while gui and sensor processes are running is not safe
            flashDrives = glob.glob("/media/pulltester/*")

            if len(flashDrives) >= 1 and connected == False:
                connected = True
                print(f"Detected new flash drive at: {flashDrives[0]}    Searching for config.yaml file")
                time.sleep(0.5)
                yamlFilePath = glob.glob(f"{flashDrives[0]}/config.yaml")[0]

                # Get the settings in config.yaml on the flash drive
                with open(yamlFilePath, "r") as f:
                    settingsDict = yaml.safe_load(f)
                
                # Update the sensor process


                # Update the GUI process
                terminalGUI.setSensors(settingsDict['selectedSensors'])

            elif len(flashDrives) == 0 and connected == True:
                connected = False
                print("Flash drive was disconnected.")



        # Begin collection
        if doCollect:
            if firstCollection:
                runNumber += 1
                firstCollection = False
                pipeMessager([parentPipe, guiParent], "read")
                time.sleep(0.1)
                data = queueReader(sensorQueue)

            newData = queueReader(sensorQueue)

            if newData != None:
                data += newData
                guiQueue.put(data)

        # Stop collection
        elif firstCollection == False:
            # Stop collection with messaging and logic vars
            firstCollection = True
            pipeMessager([parentPipe, guiParent], "stop")

            # Determine if flash drive is plugged in
            flashDrives = glob.glob("/media/pulltester/*")
        
            # Write to CSV
            if len(flashDrives) >= 1:
                writeCSV(data, runNumber, settingsDict, flashDrives[0])
            else:
                writeCSV(data, runNumber, settingsDict)

            # Clear last run from RAM
            data = []
  
if __name__ == "__main__":
    main()
