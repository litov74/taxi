import os

from config import TOKEN, ADMINS, IP


BOT_TOKEN = TOKEN

admins = ADMINS

ip = IP

aiogram_redis = {
    'host': ip,
}

redis = {
    'address': (ip, 6379),
    'encoding': 'utf8'
}
