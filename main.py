from threading import Thread
import time


from tkinter import *
from tkinter.ttk import Combobox

from manager import Manager
from fake_sensor import FakeSensor
from real_sensor import RealSensor
from gui import Gui
from network import Network


DEMO_DEVICE_NAME = 'Sensor 1'
DEMO_DEVICE_UUID = 'TEST_DEVICE'
DEMO_DEVICE_TOKEN = 'TEST_TOKEN'


window = Tk()
manager = Manager()

sensor = RealSensor(manager)
gui = Gui(manager, window, False)
network = Network(manager)

manager.setSensor(sensor)
manager.setGui(gui)
manager.setNetwork(network)

network.configure_creds(DEMO_DEVICE_UUID, DEMO_DEVICE_TOKEN)
manager.setName(DEMO_DEVICE_NAME)

sensor.start()

#Note, does not gui.boot does not return
gui.boot()
