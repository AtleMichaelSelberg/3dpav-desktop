from datetime import datetime
import requests

BASE_SERVER_URL = 'https://tdpav-backend.herokuapp.com/api/'

class Network():
    def __init__(self, manager):
        self.manager = manager

    def configure_creds(self, uuid, token):
        self.uuid = uuid
        self.token = token

    def isActive(self):
        return self.uuid and self.token

    def updateReadings(self, state):
        pass
        #r = requests.post(BASE_SERVER_URL + 'post-data-source', data={
        #    'uuid': self.uuid,
        #    'token': self.token,
        #    'value': latestPressure,
        #    'timestamp': timestamp.timestamp() * 1000,
        #    'error_message': None,
        #    'unit': 'CMH20',
        #})
