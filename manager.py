from threading import Thread
from datetime import datetime
import time
import os
import cv2


from settings import INCHES_TO_CENIMETERS, Reading


PPEAK_EXPIRATION_SECONDS = 3.0
SAMPLE_RATE_WINDOW = 5.0
READING_RELEVANCE = max([PPEAK_EXPIRATION_SECONDS, SAMPLE_RATE_WINDOW])



class Manager():
    def __init__(self):
        self.readings = []
        Thread(target=self.main_loop, args=[]).start()
    def setName(self, name):
        self.name = name
    def setSensor(self, sensor):
        self.sensor = sensor
    def setGui(self, gui):
        self.gui = gui
    def setNetwork(self, network):
        self.network = network
        
    def updateReadings(self, latestPressureValueInInches, stamp=None):
        now = datetime.now()
        self.readings = [Reading(latestPressureValueInInches * INCHES_TO_CENIMETERS, stamp or now)] + self.readings
        self.readings = [r for r in self.readings if ((now - r.stamp).total_seconds() < READING_RELEVANCE)]

    def main_loop(self):
        while True:
            self.updateReadingsSync()
            time.sleep(0.01)

    def updateReadingsSync(self):
        readings = self.readings
        if (len(readings) == 0):
            return
        latest = readings[0]

        latestPressureValue = latest.value
        latestStamp = latest.stamp
        now = datetime.now()
        
        ppeak_readings = [r for r in readings if ((now - r.stamp).total_seconds() < PPEAK_EXPIRATION_SECONDS)]
        latestPPeakValue = max([r.value for r in ppeak_readings])
        
        sample_rate_readings = [r for r in readings if ((now - r.stamp).total_seconds() < SAMPLE_RATE_WINDOW)]
        if len(sample_rate_readings) < 2:
            sampleRate = 0
        else:
            stamps_only = [r.stamp for r in sample_rate_readings]
            sampleRate = (max(stamps_only) - min(stamps_only)).total_seconds() / (len(sample_rate_readings) - 1)

        newState = {
            'latestPressureValue': latestPressureValue,
            'latestPPeakValue': latestPPeakValue,
            'sampleRate': sampleRate,
            'timestamp': latestStamp
        }
        self.network.updateReadings(newState)
        self.gui.updateReadings(newState)

    def shutdown(self):
        self.gui.shutdown()
        self.sensor.shutdown()
        os._exit(os.EX_OK)