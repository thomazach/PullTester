# Pull Tester

## Contents
1. [Quick Start Guide](https://github.com/thomazach/PullTester/tree/main#quick-start-guide)
2. [Adding Your Own Sensor](https://github.com/thomazach/PullTester/tree/main#adding-your-own-sensor)
3. [Documentation](https://github.com/thomazach/PullTester/tree/main#documentation)

# Quick Start Guide
## If you just want to use the pull tester to measure the force on the optic:
1. Get a flash drive
2. Plug it into the Reterminal (touch screen device mounted to the pull tester)
3. Push the physical green button with a circle in the bottom right to start collecting data
4. Push the same button to stop collecting data
5. The collected data will be written to a csv file on the flash drive inside of time labeled subfolders. At the highest level of the flash drive, the file structure will be:
<img width="216" alt="Screenshot 2024-07-09 at 1 52 58 PM" src="https://github.com/thomazach/PullTester/assets/86134403/874d6773-af26-4fdf-a460-e5e2322ab467">  
  
## If you want to record data from sensor configurations that are more complicated:
1. Get a flash drive
2. Plug it into the Reterminal, and wait for a message saying that the default configuration file has been copied to the flash drive.
3. Remove the flash drive and edit the default configuration on your computer
4. The default configuration file will look like this:
<img width="297" alt="Screenshot 2024-07-09 at 2 00 52 PM" src="https://github.com/thomazach/PullTester/assets/86134403/7e0cbb27-3e6b-482e-b464-c647a23735d1">
  
6. Edit the config.yaml file to your needs. It uses a [standard syntax for yaml files](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html), and the following table contains all the relevant options for this software.
  
|Key|Function|Options/Notes|  
| :---------: | :-------- | :------- |
|`columnNames`|Stores a list of strings, which will be used as the names of the columns in the csv file, with the exception that the first column is always labeled as time.|Create a new line, add a `- ` followed by a space and then the name of the next column. There is no limit to how many columns you can name.|
|`convert`|Stores a bool that tells the system if it should report raw sensor readings or convert and report proper units.|This key has only two valid values: `false` and `true`. If the key is `true`, it will display and report sensor data with units, if `false`, it will display and report raw sensor values.| 
|`sampleRate`|Sets the sample rate for the system.|This is the sample rate in Hz, and should be expressed as a float or integer, and optionally the word `null` can be used to have the system read sensors at the rate of the slowest sensor.|
|`selectedSensors`| Stores a list of strings matching the sensors you want to use. By convention, these strings are the file names and class names of sensors in the hardware abstraction layer.| Available sensor names as of writing: `hx711LoadCell`, `sinSensor`, and `cosSensor`. The last two are software testing sensors.|

### Tips
* The pull tester will automatically relaunch the python script on reboot, ssh connection, and the creation of a new terminal window. This means that if you run into an error, power cycling the system should restore it directly to a useable state.
* If you run the pull tester without a flash drive plugged in, the data will be stored on the pull tester at `$HOME/PullTester/Data` in the same format as it would have been saved on a flash drive.
* You can simply attach a mouse and keyboard to the pull tester over USB to use it like a normal raspi.
* If connected to ethernet on Caltech Secure, you can connect via ssh to retrieve data if no flash drive was present using the terminal command: `ssh pulltester@DISPLAYED-IP`. The IP of the pull tester is displayed in the terminal GUI along with the password. Note that it will display 2 IPs if on ethernet, the first is the Caltech Secure IP, and the second is the wireless IP for Caltech Visitors. Additionally, you will need to ctrl-C after ssh-ing into it.
  
# Adding Your Own Sensor
Adding your own sensor does not require an in-depth understanding of the software's architecture. The critical task is to create a python class and place it in the `sensors` folder on the pull tester. This class must have an attribute called `sensorNum`, and several methods with specific names.
A template file can be found at `sensors/Custom Sensor Format/SensorNameHere.py`. Most importantly, it includes a `read()` method which needs to read data from a sensor and return a single value, and a `convert()` function which takes a raw sensor value as input and outputs a float representing a usable unit of your choice.
Each sensor also has two constructor functions, the normal `__init__()` which runs on class creation in the main process, and the `initInProcess()` constructor which executes in the data collector process after it is started using [python's multiprocessing module](https://docs.python.org/3/library/multiprocessing.html). This `initInProcess()` method should be used when declaring 
anything outside the scope of your sensor class. If you're not familiar with python's multiprocessing library, you can likely get the behavior you desire by writing your constructor in the `initInProcess()` method, but make sure your `__init__()` constructor has the following mandatory variables: `ID`,`name`, and `maxReadFrequency`. The last step to integrate your sensor with the pull tester
is to make two small additions to `src/main.py`. First, import your new sensor class at line 22. Second, add an `elif` statement in the function `getSelectedSensors()` (line 37) that creates an instance of your new sensor if a specific string(ideally the class name of your sensor) is present in the config.yaml file.

# Documentation
The software takes advtange of python's multiprocessing library to do three tasks in parallel: reading from sensors, storing sensor data, and displaying it in the terminal in real time. The `main.py` is the entry point for the software and coordinates actions
between the two processes it creates: the data collector and gui (which are both in the `src` folder). These two processes recieve commands and settings using python's `multiprocessing.Pipe` feature, and communicate data using `multiprocessing.Queue`. When the green button on the reterminal is pressed, the main function
sends a `"read"` command to both the data collector and gui processes, at which point the data collector begins reading the sensors requested by the config file and placing them into a `Queue`. The main process continually reads from this queue, appending the new sensor readings
into a multi-dimensional array called `data`. Each time it recieves new data, it pushes the data into a different `Queue` which the gui process reads from. Having simultaneously recieved the `"read"` command, the gui process has begun updating itself (printing to the console), and waiting for data.
It reads the data and displays the last 125 data points using a terminal plotter called [asciichartpy](https://pypi.org/project/asciichartpy/). This continues until the green collection button is pressed again, which the main processes detects and sends the `"stop"` command through the parent data collector and gui pipes
at which point the data collector stops reading from sensors and the gui stops updating. The detection of this button press is done using [a python library for the reterminal](https://github.com/Seeed-Studio/Seeed_Python_ReTerminal) and runs in a dedicated thread within the main process to avoid blocking. This is simpler than having another process, since python's `threading.Thread` is 
subject to global interpreter lock and can access global variables within the main process. After the `"stop"` command is sent, the main thread use's python's csv module to write the sensor data to a csv file on the flash drive if available, or to a `Data` folder contained within the PullTester repository. The main process also detects when flash drives are connected/disconnected, and manages three behaviors: 
1. If a flash drive is plugged in and has a config.yaml file in the base directory, it updates the system to use that configuration file
2. If a flash drive is plugged in and there is no config.yaml file, use the default config.yaml file stored in this repository, and copy it to the flash drive
3. If a flash drive is disconnected, load the default config.yaml  
