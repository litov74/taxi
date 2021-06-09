import requests
from pymongo import MongoClient

from config import users
from utils.db_api.exceptions import AuthError


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
