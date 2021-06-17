import aiohttp
import sys
import logging
from config import PREFIX, users, API_TOKEN


def get_cache_id(message):
    return f'{PREFIX}_{message.from_user.id}'


def user_exists(message):
    return bool(users.count_documents({'cache_id': get_cache_id(message)}))


async def api_request(message, method, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f'https://tb.e-aristotel.com/api/{method}',
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
