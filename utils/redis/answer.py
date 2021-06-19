import json
from flask import jsonify
from config import users
from utils.db_api.cache import cache
from utils.db_api.taxi import Taxi
from utils.db_api.driver import Driver
from utils.db_api.drive import Drive, DriveСancelled
from utils.redis.create_action import create_action
from utils.redis.create_event import create_event
from utils.redis.process_answer import process_answer


def answer(data):
    from config import r, delay
    from datetime import datetime, timedelta, timezone

    def drive_create(fst, snd):
        offset = timedelta(hours=3)
        offset = timezone(offset)
        _time = (datetime.now(offset)).strftime('%Y-%m-%d %X+01:00')

        print(_time)
        _data = {'b_start_address': fst,
             'b_destination_address': snd,
             'b_start_datetime': str(_time),
             'b_car_class': '1',
             'b_payment_way': '1',
             'b_max_waiting': 3600}

        _request = taxi.createdrive({'data': json.dumps(_data)})

        _answer = {'answer': 'Поездка создана!\n'}
        full_answer = process_answer(_request, _answer)

        if full_answer == _answer:
            step['step'] = 3
            r.hmset(step_id, step)
            bid = str(_request['data']['b_id'])
            _answer['answer'] += f'Идентификатор поездки {bid}'
            full_answer = create_event(full_answer, bid, cache_id, 3, 0, prefix)
            r.hmset(step_id, {'step': 3, 'event': full_answer['subscribe']})

        return full_answer

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

    auth = cache(cache_id)

    if t == 1:
        taxi = Taxi(auth)

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
        driver = Driver(auth)

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
                    result += template_geo.format(item['b_start_latitude'], item['b_start_longitude'],
                                                  item['b_destination_latitude'], item['b_destination_longitude'],
                                                  item['b_id'])

            if result == '':
                result = 'Поездок нет'

            return {'answer': result}

        i = i.lower().strip()

        try:
            bid = i.split()[1]
        except IndexError:
            return {'answer': 'Не указан идентификатор поездки'}
        _drive = Drive(auth, bid)

        if 'взять' in i:
            u_id = driver.my_id()
            carId = driver.getCarId(u_id)
            data = {'c_id': carId, 'c_payment_way': '1'}
            resp = _drive.rule('set_performer', {'u_id': u_id, 'performer': '1', 'data': json.dumps(data)})
            return process_answer(resp, {'answer': 'Поездка получена'})
        elif 'прибыл' in i:
            resp = _drive.rule('set_arrive_state')
            return process_answer(resp, {'answer': 'Установлен статус "прибыл на место"'})
        elif 'начал' in i:
            resp = _drive.rule('set_start_state')
            return process_answer(resp, {'answer': 'Поездка начата'})
        elif 'конец' in i:
            resp = _drive.rule('set_complete_state')
            ans = {'answer': 'Поездка завершена. Поставьте оценку'}
            resp = process_answer(resp, ans)
            if resp == ans:
                resp = create_action(resp, 'set_mark', bid, cache_id, prefix)
            return resp
        elif i == 'справка':
            return {'answer': 'Справки нет, но вы держитесь )'}
        elif 'отмена' in i:
            resp = _drive.rule('set_cancel_state')
            return process_answer(resp, {'answer': 'Поездка отменена'})
        else:
            return {'answer': 'Для получения справки напишите "справка"'}
