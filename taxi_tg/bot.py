import sys
import aiohttp
import logging
from pymongo import MongoClient
from aiogram import Bot, Dispatcher, executor, types

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(message)s')

API_TOKEN = '088fb89ca58b533e41ec68d84a354abe8e9dae3c3eb1731d17ef325493da0809cd8e3a9dbd2aa74ac222a3e5da92320ee7593c837a41536a50b3d25c7b208403'
#TG_TOKEN = '1727669513:AAH7z0gOZ16uWYQSf5w-DmfgAVxGTGgjvo8'
TG_TOKEN = '1654117782:AAHXpouZAQ3wTrqk4mH940kC6YG0n1zzYMs'
PREFIX = 'tg'

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)

url = 'mongodb://heroku:f949H2FvNzxI@176.9.193.183:27017'
client = MongoClient(url, retryWrites=False)
db = client.taxi
users = db.users

def get_cache_id(message):
    return f'{PREFIX}_{message.from_user.id}'

def user_exists(message):
    return bool(users.count_documents({'cache_id': get_cache_id(message)}))    

async def api_request(message, method, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'http://127.0.0.1:5000/api/{method}',
            json={'token': API_TOKEN, 'cache_id': get_cache_id(message)} | data
        ) as response:

            ans = await response.json()
    
    logging.debug(ans)

    if 'answer' in ans:
        return ans['answer']
    elif 'error' in ans:
        return f'Ошибка: {ans["error"]}'
    else:
        return ans

@dp.message_handler(commands=['login'])
async def login(message: types.Message):
    _, login, passw = message.text.split()

    ans = await api_request(message, 'user_auth', {'login': login, 'password': passw})
    await message.answer(str(ans))

@dp.message_handler()
async def echo(message: types.Message):
    if not user_exists(message):
        return await message.answer('Необходимо войти, отправьте мне команду /login <логин> <пароль>')

    ans = await api_request(message, 'in', {'input': message.text})
    await message.answer(str(ans))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)