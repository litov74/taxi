from aiogram import Dispatcher

from config import I18N_DOMAIN, LOCALES_DIR
from .throttling import ThrottlingMiddleware
from .language import ACLMiddleware

def setup(dp: Dispatcher):
    dp.middleware.setup(ThrottlingMiddleware())
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)

