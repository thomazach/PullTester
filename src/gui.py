import asciichartpy as acp
import time
import numpy as np
import os
import subprocess

class GUI:
    """Class responsbile for creating and managing the terminal GUI"""

    def __init__(self, pipeConnection, dataQueue, sensors):
        self.pipeConnection = pipeConnection
        self.dataQueue = dataQueue
        self.sensors = sensors
        self.refresh = False # Controls if entire GUI is updated continuosly

        self.startTime = None
        self.newCmd = None

        self.data = None
        self.config = {'colors': [acp.red, acp.green, acp.yellow, acp.blue,  # All colors available to asciichartpy
                     acp.magenta, acp.cyan, acp.lightgray, acp.default,
                     acp.darkgray, acp.lightred, acp.lightgreen, acp.lightyellow,
                     acp.lightblue, acp.lightmagenta, acp.lightcyan, acp.white]}
        
        # Draw first frame on start up, clear the console for more consistent printing
        os.system("clear")
        self.drawGUI()
        

    def mainLoop(self):
        
        self.on = True
        while self.on:
            self.recieveCommand()

            if self.refresh:
                self.drawGUI()

        
    def recieveCommand(self):

        if self.pipeConnection.poll():
            self.newCmd = self.pipeConnection.recv()

        if self.newCmd == "read":
            if self.startTime == None:
                self.startTime = time.time()
                self.refresh = True

            self.read()

        if self.newCmd == "stop":
            time.sleep(0.1)
            self.read()
            self.refresh = False
            self.startTime = None
            self.newCmd = None

        if self.newCmd == "add sensor":
            self.sensors += [self.dataQueue.get()]

        if self.newCmd == "off":
            self.on = False
            self.newCmd = None

    ### Functions for commands ###
    def read(self):

        while not self.dataQueue.empty():
            self.data = self.dataQueue.get()

    def drawGUI(self):
        """Draws a single 'frame' of the GUI.
        Note: It's important to create a single string to print once, so that terminal
        autoscroll is minimized and reaches a 'steady state' where the terminal tries to get
        all of the new information in the window."""

        ## Header information ##
        GUIString = "Pull Tester \nCurrent LAN accessible IP: "
        ip = subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE).stdout.decode('utf-8')[:-2] # Removes the \n
        GUIString += ip

        ## Button reminder/instructions
        GUIString += f"        Press the {acp.lightgreen}O{acp.reset} button to begin/stop collecting data.\n"

        # TODO: Print IP address
        # TODO: Print available and selected sensors

        # Create graph data
        if self.startTime != None:
            terminalGraphData = [0]

            if self.data != None:
                now = time.time() - self.startTime
                terminalGraphData = np.array(self.data)[-125:, 1:].T.tolist()

            # Print/display graph data
            GUIString += acp.plot(terminalGraphData, self.config) + '\n'

            # Print x-axis
            GUIString += "          ----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|\n"
            if self.data != None:
                GUIString += f"Time elapsed: {now:.2f}\n"

        # Legend (display it always to show which sensors are connected)
        GUIString += "Current Sensors:\n"
        for sensor, color in zip(self.sensors, self.config['colors']):
            GUIString += f"{color}{sensor.name} \033[0m\n"

        print(GUIString)



