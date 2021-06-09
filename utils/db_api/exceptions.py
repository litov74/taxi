class DriveСancelled(Exception):
    def __init__(self):
        self.txt = 'Поездка была отменена'


class ApiException(Exception):
    def __init__(self):
        self.txt = 'Ошибка api'


class AuthError(Exception):
    def __init__(self, message):
        self.txt = 'Ошибка авторизации'
        self.message = message
