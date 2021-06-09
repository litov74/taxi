import requests

from utils.db_api.exceptions import DriveСancelled


class Drive:
    def __init__(self, auth, bid:str):
        self.auth = auth
        self.bid = str(bid)

    def wait(self, state, n=0):
        while True:
            data = self.get()
            data = data['data']['booking'][self.bid]
            if data['drivers'] is not None:
                try:
                    data = data['drivers'][n]['c_state']
                    if state == '2':
                        return data
                    elif state <= int(data):
                        return data
                    elif data == '2':
                        raise DriveСancelled
                except IndexError:
                    pass

    def get(self):
        data = self.auth
        data['array_type'] = 'list'
        r = requests.post('https://ibronevik.ru/taxi/api/v1/drive/get/' + self.bid, data)
        return r.json()

    def driver_info(self):
        data = self.get()
        driver_id = data['data']['booking'][self.bid]['drivers'][0]['u_id']
        driver = requests.post('https://ibronevik.ru/taxi/api/v1/user/' + driver_id, self.auth).json()
        driver = driver['data']['user'][driver_id]

        return driver

    def rule(self, action, data={}):
        data['action'] = action
        for value in self.auth:
            data[value] = self.auth[value]
        print(data)
        r = requests.post('https://ibronevik.ru/taxi/api/v1/drive/get/' + self.bid, data)
        return r.json()
