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
from sensors.hx711LoadCell import hx711LoadCell

### Core Component Imports ###
from src.gui import GUI
from src.dataCollector import dataCollector

def loadYaml(path):
    with open(path, "r") as f:
        contents = yaml.safe_load(f)
    
    return contents

def getSelectedSensors(sensorNames: list[str]):
    """Match sensor string names with instances of their respective sensor objects"""

    selectedSensors = []
    for sensorName in sensorNames:
        # Using if elif since hardware is running on python 3.9.2 and upgrading just for match case is not worth it
        if sensorName == "sinSensor":
            selectedSensors += [sinSensor()]
        
        elif sensorName == "cosSensor":
            selectedSensors += [cosSensor()]

        elif sensorName == "hx711LoadCell":
            selectedSensors += [hx711LoadCell()]

    return selectedSensors

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

def updateSystem(configPath: str, oldSensors, dataPipe, GUIPipe):
    """Updates entire system with new configuration settings specified in config.yaml"""

    for sensor in oldSensors:
        sensor.reset()

    settingsDict = loadYaml(configPath)
    selectedSensors = getSelectedSensors(settingsDict['selectedSensors'])
                
    # Update the sensor process
    dataPipe.send("set sensors")
    dataPipe.send(selectedSensors)
    dataPipe.send("set settings")
    dataPipe.send(settingsDict)

    # Update the GUI process
    GUIPipe.send("set sensors")
    GUIPipe.send(selectedSensors)

    return selectedSensors # Return the sensors so that they can be passed back into this function if the flashdrive is plugged back in
    

# Global scope variable used for terminal control
doCollect = False
def main():

    ### Load settings from default config file ###
    settingsDict = loadYaml("config.yaml")
    selectedSensors = getSelectedSensors(settingsDict['selectedSensors'])
    
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
                yamlFilePath = glob.glob(f"{flashDrives[0]}/config.yaml")

                if len(yamlFilePath) != 0: # There is a custom config.yaml file on the flash drive
                    print("Found a config file on the flashdrive, this config will be used while flashdrive is connected.")
                    
                    selectedSensors = updateSystem(yamlFilePath[0], selectedSensors, parentPipe, guiParent)

                else: # There isn't a custom yaml file and we need to put a copy of the default one onto the flash drive
                    print("The config.yaml file couldn't be found on the first level of the flashdrive. A copy of the default configuration has been copied to the flashdrive.")
                    os.system(f"cp config.yaml {flashDrives[0]}/config.yaml")


            elif len(flashDrives) == 0 and connected == True:
                connected = False
                print("Flash drive was disconnected, using the defualt config file.")

                selectedSensors = updateSystem("config.yaml", selectedSensors, parentPipe, guiParent)


        # Begin collection
        if doCollect:
            if firstCollection:
                runNumber += 1
                firstCollection = False
                pipeMessager([parentPipe, guiParent], "read")
                
                # Wait for actual data to arrive
                data = None
                while data == None:
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
