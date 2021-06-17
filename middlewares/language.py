from typing import Tuple, Any

from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from config import I18N_DOMAIN, LOCALES_DIR


async def get_language(user_id):
    pass

class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> str:
        user = types.User.get_current()
        return await get_language(user.id) or user.locale
