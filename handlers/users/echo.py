
from aiogram import types
from handlers.users.user_activities import user_exists, api_request
from loader import dp


@dp.message_handler()
async def echo(message: types.Message):
    if not user_exists(message):
        return await message.answer('Необходимо войти, отправьте мне команду /login <логин> <пароль>')

    ans = await api_request(message, 'in', {'input': message.text})
    await message.answer(str(ans))