from datetime import datetime

class Gui():
    def __init__(self, manager):
        self.manager = manager

    def setup_gui(self):
        #Julia creates GUI here
        print('Creating GUI')

    def updateReadings(self, timestamp, latestPressure, latestPPeak):
        print('Latest Pressure: {0}. Latest PPeak: {1}. Lag (ms): {2:0.2f}'.format(
            latestPressure, latestPPeak, (datetime.now() - timestamp).total_seconds() * 1000))
        #Julia updates GUI here
