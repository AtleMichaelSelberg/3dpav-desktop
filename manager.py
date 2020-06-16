from threading import Thread
from datetime import datetime


PPEAK_EXPIRATION_SECONDS = 3.0


class Reading():
    def __init__(self, value, stamp):
        self.value = value
        self.stamp = stamp


class Manager():
    def __init__(self):
        self.readings = []
    def setName(self, name):
        self.name = name
    def setSensor(self, sensor):
        self.sensor = sensor
    def setGui(self, gui):
        self.gui = gui
    def setNetwork(self, network):
        self.network = network

    def updateReadings(self, latestPressureValue, stamp=None):
        stamp = stamp or datetime.now()
        Thread(target=self.updateReadingsSync, args=[{
            'value': latestPressureValue,
            'stamp': stamp
        }]).start()

    def updateReadingsSync(self, params):
        self.latestPressureValue = params.get('value')
        stamp = params.get('stamp')
        now = datetime.now()
        
        self.readings.append(Reading(self.latestPressureValue, stamp))
        self.readings = [r for r in self.readings if ((now - r.stamp).total_seconds() < PPEAK_EXPIRATION_SECONDS)]
        self.latestPPeakValue = max([r.value for r in self.readings])
        
        updateParams = {
            'latestPressureValue': self.latestPressureValue,
            'latestPPeakValue': self.latestPPeakValue,
            'timestamp': stamp
        }
        if (self.gui):
            Thread(target=self.updateGuiSync, args=[updateParams]).start()
        if (self.network and self.network.isActive()):
            Thread(target=self.postToNetworkSync, args=[updateParams]).start()

    def postToNetworkSync(self, params):
        latestPressureValue = params.get('latestPressureValue')
        latestPPeakValue = params.get('latestPPeakValue')
        timestamp = params.get('timestamp')
        self.network.updateReadings(timestamp, latestPressureValue)

    def updateGuiSync(self, params):
        latestPressureValue = params.get('latestPressureValue')
        latestPPeakValue = params.get('latestPPeakValue')
        timestamp = params.get('timestamp')
        self.gui.updateReadings(timestamp, latestPressureValue, latestPPeakValue)
