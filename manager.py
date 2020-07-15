from threading import Thread
from datetime import datetime
from settings import INCHES_TO_CENIMETERS, Reading


PPEAK_EXPIRATION_SECONDS = 3.0
SAMPLE_RATE_WINDOW = 5.0
READING_RELEVANCE = max([PPEAK_EXPIRATION_SECONDS, SAMPLE_RATE_WINDOW])



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

    def updateReadings(self, latestPressureValueInInches, stamp=None):
        stamp = stamp or datetime.now()
        Thread(target=self.updateReadingsSync, args=[{
            'value': latestPressureValueInInches * INCHES_TO_CENIMETERS,
            'stamp': stamp
        }]).start()

    def updateReadingsSync(self, params):
        self.latestPressureValue = params.get('value')
        stamp = params.get('stamp')
        now = datetime.now()
        
        self.readings.append(Reading(self.latestPressureValue, stamp))
        self.readings = [r for r in self.readings if ((now - r.stamp).total_seconds() < READING_RELEVANCE)]
        
        ppeak_readings = [r for r in self.readings if ((now - r.stamp).total_seconds() < PPEAK_EXPIRATION_SECONDS)]
        self.latestPPeakValue = max([r.value for r in ppeak_readings])
        
        sample_rate_readings = [r for r in self.readings if ((now - r.stamp).total_seconds() < SAMPLE_RATE_WINDOW)]
        if len(sample_rate_readings) < 2:
            self.sampleRate = 0
        else:
            stamps_only = [r.stamp for r in sample_rate_readings]
            self.sampleRate = (max(stamps_only) - min(stamps_only)).total_seconds() / (len(sample_rate_readings) - 1)

        updateParams = {
            'latestPressureValue': self.latestPressureValue,
            'latestPPeakValue': self.latestPPeakValue,
            'sampleRate': self.sampleRate,
            'timestamp': stamp
        }
        if (self.gui):
            Thread(target=self.updateGuiSync, args=[updateParams]).start()
        if (self.network and self.network.isActive()):
            Thread(target=self.postToNetworkSync, args=[updateParams]).start()

    def postToNetworkSync(self, params):
        latestPressureValue = params.get('latestPressureValue')
        latestPPeakValue = params.get('latestPPeakValue')
        sampleRate = params.get('sampleRate')
        timestamp = params.get('timestamp')
        self.network.updateReadings(timestamp, latestPressureValue)

    def updateGuiSync(self, params):
        latestPressureValue = params.get('latestPressureValue')
        latestPPeakValue = params.get('latestPPeakValue')
        sampleRate = params.get('sampleRate')
        timestamp = params.get('timestamp')
        self.gui.updateReadings(timestamp, latestPressureValue, latestPPeakValue, sampleRate)
