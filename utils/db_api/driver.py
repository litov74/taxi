import requests


class Driver:
    def __init__(self, auth):
        self.auth = auth

    def my_id(self):
        r = requests.post('https://ibronevik.ru/taxi/api/v1/user', self.auth).json()
        if r['status'] == 'success':
            u_id = r['auth_user']['u_id']
            return u_id

    def getCarId(self, userId):
        r = requests.post('https://ibronevik.ru/taxi/api/v1/user/' + userId + '/car', self.auth).json()
        if r['status'] == 'success':
            u_id = list(r['data']['car'].keys())
            return u_id[0]

    def now(self):
        data = {'array_type': 'list'}
        for value in self.auth:
            data[value] = self.auth[value]
        r = requests.post('https://ibronevik.ru/taxi/api/v1/drive/now', data)
        return r.json()['data']['booking']

    def listen(self):
        # криво работает
        while True:
            data = self.now()
            if data != []:
                yield data
