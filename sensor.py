from threading import Thread


class Sensor():
    def __init__(self, manager):
        self.manager = manager

    def start(self):
        Thread(target=self.run, args=[]).start()
