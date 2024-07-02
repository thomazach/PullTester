import asciichartpy as acp
import time
import numpy as np

class GUI:
    """Class responsbile for creating and managing the terminal GUI"""

    def __init__(self, pipeConnection, dataQueue):
        self.pipeConnection = pipeConnection
        self.dataQueue = dataQueue
        self.sensors = []
        self.refresh = False # Controls if entire GUI is updated continuosly

        self.startTime = None
        self.newCmd = None

        self.data = None
        self.config = {'colors': [acp.red, acp.green, acp.yellow, acp.blue,  # All colors available to asciichartpy
                     acp.magenta, acp.cyan, acp.lightgray, acp.default,
                     acp.darkgray, acp.lightred, acp.lightgreen, acp.lightyellow,
                     acp.lightblue, acp.lightmagenta, acp.lightcyan, acp.white],
                     'min': -3, 'max': 3}
        
        # Draw first frame on start up
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

        ## Header information ##
        print("Pull Tester")
        # TODO: Print IP address
        # TODO: Print available and selected sensors

        # Create graph data
        if self.startTime != None:
            terminalGraphData = [0]

            if self.data != None:
                now = time.time() - self.startTime
                thirtySecondsAgo = now - 10

                for i, row in enumerate(self.data):
                    timeOfMeasurement = row[0]
                    #print(self.data)
                    #print(row[0])
                    if timeOfMeasurement < thirtySecondsAgo:
                        self.data.pop(i)

                terminalGraphData = np.array(self.data)[:, 1:].T.tolist()

            # Print/display graph data
            print(acp.plot(terminalGraphData, self.config))

            # Print x-axis
            print(f"          ----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|")
            if self.data != None:
                print(f"Time elapsed: {now}")

            # Legend
            print("Graph Legend:")
            for sensor, color in zip(self.sensors, self.config['colors']):
                print(f"{color}{sensor.name}\n")
                print("\033[0m")




