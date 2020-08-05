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
DEMO_DEVICE_UUID = '5812a20548ee4c5398be1e53127e8ad1'
DEMO_DEVICE_TOKEN = 'JqHJ1jHGnOOyt1DHt7LtlSQskNfvNrbGM3YALl7QxyW9wjjJ6oE0pderEZYB5phsLehgsEoKUVudv1mTusAHEW0TjPA1SwV2m3iY2JFKbi3LJECzps9YJOXWzkqkKPnZ'


window = Tk()
manager = Manager()

sensor = FakeSensor(manager)
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
