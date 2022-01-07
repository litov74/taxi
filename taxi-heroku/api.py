import os
import json
import requests
from pymongo import MongoClient

class DriveСancelled(Exception):
    def __init__(self):
        self.txt = 'Поездка была отменена'

class ApiException(Exception):
    def __init__(self):
        self.txt = 'Ошибка api'

class AuthError(Exception):
    def __init__(self, message):
        self.txt = 'Ошибка авторизации'
        self.message = message

def cache(c_id):
    t = users.find_one({"cache_id": c_id})['auth']

    return t

url = 'mongodb://heroku:f949H2FvNzxI@176.9.193.183:27017'
client = MongoClient(url, retryWrites=False)
db = client.taxi
users = db.users

class Taxi:
    def __init__(self, auth):
        self.auth = auth

    def auth(l, p, cache_id):
        if '@' in l:
            t = 'e-mail'
        else:
            t = 'phone'

        s = requests.session()
        r = s.post('https://ibronevik.ru/taxi/api/v1/auth/', {'login': l,'password': p, 'type': t}).json()
        if r['status'] == 'success':
            cache = users.find_one({"cache_id": cache_id})

            if not cache:
                r = s.get('https://ibronevik.ru/taxi/api/v1/token').json()
                auth = r['data']
                role = int(r['auth_user']['u_role'])

                user = {'cache_id': cache_id, 'auth': auth, 'role': role}

                users.insert_one(user)
            else:
                user = cache

            r = user['auth']
            r['cache_id'] = cache_id
            r['role'] = user['role']

            return r

        else:
            if 'message' in r:
                message = r['message']
            else:
                message = ''

            raise AuthError(message)

    def createdrive(self, data):
        for value in self.auth:
            data[value] = self.auth[value]
        r = requests.post('https://ibronevik.ru/taxi/api/v1/drive', data)
        return r.json()

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

        return driver6

    def rule(self, action, data={}):
        data['action'] = action
        for value in self.auth:
            data[value] = self.auth[value]
        print(data)
        r = requests.post('https://ibronevik.ru/taxi/api/v1/drive/get/' + self.bid, data)
        return r.json()

class Driver:
    def __init__(self, auth):
        self.auth = auth

    def my_id(self):
        r = requests.post('https://ibronevik.ru/taxi/api/v1/user', self.auth).json()
        if r['status'] == 'success':
            u_id = r['auth_user']['u_id']
            return u_id
    
    def getCarId(self, userId):
        r = requests.post('https://ibronevik.ru/taxi/api/v1/user/'+ userId +'/car', self.auth).json()
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

if __name__ == '__main__':
    #print(Taxi.auth('someemail@topmail1.net','3Ll39R!g4L', 'dev_1'))
    #print(Taxi.auth('someemail@topmail1.net','3Ll39R!g4', '4'))
    #Taxi.auth('kaboc78492@nwesmail.com','kix+PNDU$[', 'dev_2')
    #Taxi.auth('cohogo2704@tastrg.com','@^!*C[B!|[', 'dev_3')
    pass