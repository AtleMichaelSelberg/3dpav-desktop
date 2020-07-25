import time
import random

from sensor import Sensor


class FakeSensor(Sensor):
    def __init__(self, manager):
        super().__init__(manager)

    def run(self):
        while True:
            self.manager.updateReadings(random.randint(10, 30))
            time.sleep(0.1)
