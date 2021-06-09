
from aiogram import types
from handlers.users.user_activities import api_request
from loader import dp


@dp.message_handler(commands=['login'])
async def login(message: types.Message):
    _, login, passw = message.text.split()

    ans = await api_request(message, 'user_auth', {'login': login, 'password': passw})
    await message.answer(str(ans))
