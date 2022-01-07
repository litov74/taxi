import os
import json
import hashlib
import api
import redis
import requests

from time import sleep, time
from datetime import datetime, timedelta, timezone
from threading import Thread
from pymongo import MongoClient

from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
from flask_cors import CORS

domain = 'https://tb.e-aristotel.com'

app = Flask(__name__, static_folder='static')
cors = CORS(app, resources={r"/service/*": {"origins": domain}, r"/api/*": {"origins": '*'}})

url = 'mongodb://heroku:f949H2FvNzxI@176.9.193.183:27017'
client = MongoClient(url, retryWrites=False)
db = client.taxi
users = db.users
tokens = db.tokens

delay = 2.5 #10

r = redis.from_url('redis://127.0.0.1:6379', decode_responses=True)

def check_token(token, prefix):
    global tokens

    res = tokens.find_one({'token': token})
    if res:
        if res['prefix'] == prefix:
            return True
    
    return False

def process_answer(data, answer):
    if data['status'] == 'success':
        return answer
    elif data['status'] == 'error':
        if 'message' in data:
            return {'error': f'Произошла ошибка: "{data["message"]}"'}
        else:
            return {'error': 'Произошла неизвестная ошибка'}
    else:
        return {'error': 'Произошла неизвестная ошибка'}

def create_action(arr, type, bid, cache_id, prefix):
    global r

    arr['action'] = type
    action_id = f'{prefix}_{time()}_{bid}'
    action_url = f'{domain}/api/action/{action_id}'
    r.hmset(f'action_{action_id}', {'type': type, 'cache_id': cache_id, 'bid': bid, 'prefix': prefix})
    arr['action_url'] = action_url

    return arr

def create_event(arr, bid, cache_id, code, n, prefix):
    global r
    global domain
    global delay

    event_id = f'{prefix}_{time()}_{bid}'
    expires = time() + 600
    r.hmset(f'event_{event_id}', {'bid': bid, 'cache_id': cache_id, 'code': code, 'expires': expires, 'n': n, 'prefix': prefix})

    arr['subscribe'] = f'{domain}/api/event/{event_id}'
    arr['delay'] = delay

    return arr

def answer(data):
    global r
    global delay

    def drive_create(fst, snd):
            offset = timedelta(hours=3)
            offset = timezone(offset)
            t = (datetime.now(offset)).strftime('%Y-%m-%d %X+01:00')

            print(t)
            d = {'b_start_address': fst,
                 'b_destination_address': snd,
                 'b_start_datetime': str(t),
                 'b_car_class': '1',
                 'b_payment_way': '1',
                 'b_max_waiting': 3600}

            req = taxi.createdrive({'data': json.dumps(d)})

            ans = {'answer': 'Поездка создана'}
            a = process_answer(req, ans)

            if a == ans:
                step['step'] = 3
                r.hmset(step_id, step)
                bid = str(req['data']['b_id'])
                ans['answer'] += f' Идентификатор поездки {bid}'
                a = create_event(a, bid, cache_id, 3, 0, prefix)
                r.hmset(step_id, {'step': 3, 'event': a['subscribe']})

            return a

    cache_id = str(data['cache_id'])
    prefix = cache_id.split('_')[0]

    step_id = f'step_{cache_id}'
    step = r.hgetall(step_id)

    if not step:
        step = {'step': 0}
        r.hmset(step_id, {'step': 0})

    user = users.find_one({"cache_id": cache_id})

    if not user:
        return jsonify({'error': 'Пользователь не найден'})
    else:
        t = user['role']

    auth = api.cache(cache_id)

    if t == 1:
        taxi = api.Taxi(auth)

        try:
            i = data['input']
        except KeyError:
            return jsonify({'error': 'Не передан input'})

        t = i.lower().strip()
        print(f'{step = }')
        c_step = int(step['step'])
        print(f'{c_step = }')
        print(f'{t = }')
        if c_step == 0 and t == 'заказать':
            step['step'] = 1
            r.hmset(step_id, step)
            return {'answer': 'Откуда'}

        elif c_step == 0 and t.startswith('заказать'):
            if ';' in i:
                i = i.split()
                fst = i[1].strip(';')
                snd = i[2].strip(';')
                return drive_create(fst, snd)

        elif c_step == 1:
            step['fst'] = i
            step['step'] = 2
            r.hmset(step_id, step)
            return {'answer': 'Куда'}
            
        elif c_step == 2:
            step['snd'] = i
            step['step'] = 3
            r.hmset(step_id, step)

            fst = step['fst']
            snd = step['snd']
            return drive_create(fst, snd)

        elif c_step == 3:
            a = {'answer': 'Дождитесь завершения предыдущей поездки', 'act_event': step['event'], 'delay': delay}
            return a

        else:
            return {'answer': 'Для заказа такси напишите "заказать"'}

    elif t == 2:
        driver = api.Driver(auth)

        i = data['input']

        if 'список' in i.lower().strip():
            result = ''
            template = 'Поездка из "{}" в "{}" id {}\n'
            template_geo = 'Поездка по геолокации начало {} {}, конец {} {}\n'
            answer = driver.now()

            for item in answer:
                if (item['b_start_address'] != '' and
                        item['b_destination_address'] != ''):
                    result += template.format(item['b_start_address'], item['b_destination_address'], item['b_id'])
                elif (item['b_start_latitude'] != '' and
                        item['b_start_longitude'] != '' and
                        item['b_destination_latitude'] != '' and
                        item['b_destination_longitude'] != ''):
                    result += template_geo.format(item['b_start_latitude'], item['b_start_longitude'], item['b_destination_latitude'], item['b_destination_longitude'], item['b_id'])
            
            if result == '':
                result = 'Поездок нет'

            return {'answer': result}

        i = i.lower().strip()

        try:
            bid = i.split()[1]
        except IndexError:
            return {'answer': 'Не указан идентификатор поездки'}
        d = api.Drive(auth, bid)

        if 'взять' in i:
            u_id = driver.my_id()
            carId = driver.getCarId(u_id)
            data = {'c_id': carId, 'c_payment_way': '1'}
            resp = d.rule('set_performer', {'u_id': u_id, 'performer': '1', 'data': json.dumps(data)})
            return process_answer(resp, {'answer': 'Поездка получена'})
        elif 'прибыл' in i:
            resp = d.rule('set_arrive_state')
            return process_answer(resp, {'answer': 'Установлен статус "прибыл на место"'})
        elif 'начал' in i:
            resp = d.rule('set_start_state')
            return process_answer(resp, {'answer': 'Поездка начата'})
        elif 'конец' in i:
            resp = d.rule('set_complete_state')
            ans = {'answer': 'Поездка завершена. Поставьте оценку'}
            resp = process_answer(resp, ans)

            if resp == ans:
                resp = create_action(resp, 'set_mark', bid, cache_id, prefix)
            return resp
        elif i == 'справка':
            return {'answer': 'Справки нет, но вы держитесь )'}
        elif 'отмена' in i:
            resp = d.rule('set_cancel_state')
            return process_answer(resp, {'answer': 'Поездка отменена'})
        else:
            return {'answer': 'Для получения справки напишите "справка"'}

@app.route('/api/in', methods=['post', 'options'])
def inp():
    data = request.json
    if not data:
        data = {}

    try:
        token = data['token']
    except KeyError:
        token = ''

    try:
        cache_id = str(data['cache_id'])
    except KeyError:
        return jsonify({'error': 'Не передан cache_id'})

    prefix = cache_id.split('_')[0]

    if not check_token(token, prefix):
        return jsonify({'error': 'Неверный токен'}), 403

    r = answer(data)

    print(r)
    return (r)

@app.route('/api/event/<event>', methods=['post', 'options'])
def process_event(event):
    global r

    data = request.json
    if not data:
        data = {}

    resp = {'event': event}
    msgs = {2: 'Поездка отменена', 3: 'Поездка принята', 4: 'Водитель прибыл на место',
            5: 'Начало поездки', 6: 'Поездка завершена. Поставьте оценку'}

    try:
        token = data['token']
    except KeyError:
        token = ''

    prefix = event.split('_')[0]

    # if not check_token(token, prefix):
    #    return jsonify({'error': 'Неверный токен', 'status': 'not_authorized'}), 403

    e = r.hgetall(f'event_{event}')
    
    cache_id = e['cache_id']
    step_id = f'step_{cache_id}'

    if e:
        if time() < float(e['expires']):
            bid = e['bid']

            code = int(e['code'])
            n = int(e['n'])

            auth = api.cache(cache_id)
            drive = api.Drive(auth, bid)

            d = drive.get()
            if d['status'] == 'success':
                d = d['data']['booking'][0]

                if d['drivers']:
                    try:
                        driver = d['drivers'][n]
                        state = int(driver['c_state'])
                        if state >= code:
                            resp['status'] = 'comlete'
                        elif state == 2:
                            resp['status'] = 'comlete'
                    except IndexError:
                        pass
                
                    if 'status' in resp:
                        if resp['status'] == 'comlete':
                            r.delete(f'event_{event}')
                            resp['message'] = msgs[state]
                            if state == 2:
                                code = 3
                                n += 1
                                resp = create_event(resp, bid, cache_id, code, n)
                                r.hmset(step_id, {'step': 3, 'event': resp['subscribe']})
                                #resp['message'] += '. Вас повезёт'

                            elif code < 6:
                                expires = time() + 600
                                code += 1
                                resp = create_event(resp, bid, cache_id, code, n, prefix)
                                r.hmset(step_id, {'step': 3, 'event': resp['subscribe']})

                            elif code == 6:
                                r.hmset(step_id, {'step': 0})
                                resp = create_action(resp, 'set_mark', bid, cache_id, prefix)

                if not 'status' in resp:
                    resp['status'] = 'wait'
                    resp['delay'] = delay
        else:
            r.delete(f'event_{event}')
            r.hmset(step_id, {'step': 0})
            resp['status'] = 'expired'
            resp['message'] = 'Прошло слишком много времени. Событие просрочено'
    else:
        resp['status'] = 'not_found'
        resp['message'] = 'Событие не найдено'
       
    print(resp)
    return jsonify(resp)

@app.route('/api/action/<action>', methods=['post', 'options'])
def process_action(action):
    global r

    data = request.json
    print(data)
    if not data:
        data = {}

    try:
        token = data['token']
    except KeyError:
        token = ''

    prefix = action.split('_')[0]

    if not check_token(token, prefix):
        return jsonify({'error': 'Неверный токен'}), 403

    act = r.hgetall(f'action_{action}')
    
    if act:
        action_type = act['type']

        if action_type == 'set_mark':
            cache_id = act['cache_id']
            bid = act['bid']

            if 'value' in data:
                value = data['value']
            else:
                ans = {'error': 'Не передан value'}
                return jsonify(ans)

            auth = api.cache(cache_id)
            drive = api.Drive(auth, bid)
            resp = drive.rule('set_rate', {'value': value})
            print(f'{resp = }')
            ans = {'answer': f'Оценка {value} поставлена', 'final': True}

            resp = process_answer(resp, ans)
            if resp == ans:
                r.delete(f'action_{action}')
            
            print(resp)
            return jsonify(resp)

    else:
        return jsonify({'error': 'Действие не найдено'}), 404

@app.route('/api/user_auth', methods=['post', 'options'])
def auth():
    data = request.json

    try:
        token = data['token']
    except KeyError:
        token = ''
    
    if 'cache_id' in data:
        cache_id = data['cache_id']
    else:
        return jsonify({'error': 'Не передан cache_id'})

    prefix = cache_id.split('_')[0]

    if not check_token(token, prefix):
        return jsonify({'error': 'Неверный токен'}), 403

    if 'login' in data:
        l = data['login']
    else:
        return jsonify({'error': 'Не передан login'})
    if 'password' in data:
        p = data['password']
    else:
        return jsonify({'error': 'Не передан password'})

    try:
        api.Taxi.auth(l, p, cache_id)
        r = {'answer': 'Вы успешно авторизовались'}
    except api.AuthError as e:
        r = {'error': e.message}
    
    print(r)
    return jsonify(r)

@app.route('/service/token_admin_auth', methods=['post', 'options'])
def token_auth():
    data = request.json
    if not data:
        data = {}
    
    if 'service_token' in data:
        service_token = data['service_token']
    else:
        return jsonify({'error': 'Не передан service_token'})

    if 'g-recaptcha-response' in data:
        recaptcha = data['g-recaptcha-response']
        t = requests.post('https://www.google.com/recaptcha/api/siteverify', 
                          {'secret': '6LekRaoZAAAAANxEjYiFH4EJvLVLFuazhx814W4Y', 'response': recaptcha}).json()
        if t['success'] == False:
            return jsonify({'error': 'Не пройдена проверка reCaptcha'})
    else:
        return jsonify({'error': 'Не передан g-recaptcha-response'})

    orig = tokens.find_one({'prefix': 'service'})
    if service_token != orig['token']:
        return jsonify({'error': 'Неверный токен'})
    else:
        response.set_cookie('service_token', service_token, secure=True, httponly=True, path='/admin/tokens', max_age=31557600, samesite='lax')
        return {'authorized': True}

def check_servise_data(data):
    if not data:
        data = {}

    if 'service_token' in data:
        service_token = data['service_token']
    else:
        return jsonify({'error': 'Не передан service_token'})

    orig = tokens.find_one({'prefix': 'service'})
    if service_token != orig['token']:
        return jsonify({'error': 'Неверный токен'})

    if 'prefix' in data:
        prefix = data['prefix']
        data['prefix'] = prefix.lower().strip()
    else:
        return jsonify({'error': 'Не передан prefix'})

    if not prefix:
        return jsonify({'error': 'Не передан prefix'})

    return jsonify(data)

@app.route('/service/generate_token', methods=['post', 'options'])
def gen_token():
    data = request.json

    data = check_servise_data(data)
    if 'error' in data:
        return jsonify(data)
    prefix = data['prefix']

    r = tokens.find_one({'prefix': prefix})

    if r:
        return jsonify({'error': 'prefix занят'})
    else:
        dt = str(datetime.utcnow())
        token = f'{prefix} {dt} taxi token'.encode()
        token = hashlib.sha512(token).hexdigest()

        t = {'prefix': prefix, 'token': token, 't': dt, 'ip': request.remote_addr}
        r = tokens.insert_one(t)
        if r.inserted_id:
            return jsonify({'token': token})
        else:
            return jsonify({'error': 'Ошибка записи в БД'})

@app.route('/service/revoke_token', methods=['post', 'options'])
def revoke_token():
    data = request.json

    data = check_servise_data(data)
    if 'error' in data:
        return data
    prefix = data['prefix']
    
    r = tokens.find_one({'prefix': prefix})

    if not r:
        return jsonify({'error': 'prefix не найден'})
    elif prefix == 'service':
        return jsonify({'error': 'Невозможно отозвать сервисный токен'})
    else:
        r = tokens.delete_one({'prefix': prefix})
        if r.deleted_count > 0:
            return jsonify({'revoked': 'Токен отозван'})
        else:
            return jsonify({'error': 'Ошибка записи в БД'})
       
@app.route('/service/refresh_token', methods=['post', 'options'])
def refresh_token():
    data = request.json

    data = check_servise_data(data)
    if 'error' in data:
        return data
    prefix = data['prefix']

    r = tokens.find_one({'prefix': prefix})

    if not r:
        return jsonify({'error': 'prefix не найден'})
    elif prefix == 'service':
        return jsonify({'error': 'Невозможно отозвать сервисный токен'})
    else:
        dt = str(datetime.utcnow())
        new = f'{prefix} {dt} taxi token'.encode()
        new = hashlib.sha512(new).hexdigest()

        r = tokens.update_one({'prefix': prefix}, {'$set': {'token': new, 't': dt, 'ip': request.remote_addr}})

        if r.modified_count > 0:
            return jsonify({'token': new})
        else:
            return jsonify({'error': 'Ошибка записи в БД'})

@app.route('/service/refresh_service_token', methods=['post', 'options'])
def refresh_service_token():
    data = request.json
    if not data:
        data = {}

    if 'service_token' in data:
        service_token = data['service_token']
    else:
        return jsonify({'error': 'Не передан service_token'})
    
    orig = tokens.find_one({'prefix': 'service'})
    if service_token != orig['token']:
        return jsonify({'error': 'Неверный токен'})

    dt = str(datetime.utcnow())
    new = f'service {dt} taxi service token'.encode()
    new = hashlib.sha512(new).hexdigest()

    r = tokens.update_one({'prefix': 'service'}, {'$set': {'token': new}})

    if r.modified_count > 0:
        return jsonify({'token': new})
    else:
        return jsonify({'error': 'Ошибка записи в БД'})

@app.route('/service', methods=['get', 'options'])
def index():
    return app.send_static_file('index.html')

@app.route('/service/docs', methods=['get', 'options'])
def docs():
    return app.send_static_file('docs.html')

@app.route('/service/admin/tokens', methods=['get', 'options'])
def tokens_admin():
    service_token = request.cookies.get('service_token', '')
    
    orig = tokens.find_one({'prefix': 'service'})
    if service_token != orig['token']:
        return app.send_static_file('tokens_admin_auth.html')
    else:
        t = list(tokens.find({}))
        return app.send_static_file('tokens_admin.html', tokens = t, service_token = service_token)

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()

    response.data = json.dumps({
        "error": e.code,
        "traceback": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
