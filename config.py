from pathlib import Path

from pymongo import MongoClient
from flask import Flask
from flask_cors import CORS
import redis


TOKEN = "1170817945:AAHrj2ZGVo9V9lQynQdG4p_-8AVuFiLFwB4"

ADMINS = ["598522198", ]

IP = "localhost"

url = 'mongodb://heroku:f949H2FvNzxI@176.9.193.183:27017'

#url = 'mongodb://localhost:27017'

client = MongoClient(url, retryWrites=False)
db = client.taxi
users = db.users
tokens = db.tokens

PREFIX = 'tg'

API_TOKEN = '088fb89ca58b533e41ec68d84a354abe8e9dae3c3eb1731d17ef325493da0809cd8e3a9dbd2aa74ac222a3e5da92320ee7593c837a41536a50b3d25c7b208403'

domain = 'https://tb.e-aristotel.com'

app = Flask(__name__, static_folder='static')
cors = CORS(app, resources={r"/service/*": {"origins": domain}, r"/api/*": {"origins": '*'}})

delay = 2.5 #10

r = redis.from_url('redis://127.0.0.1:6379', decode_responses=True)

I18N_DOMAIN = "taxi_bot"
BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'

