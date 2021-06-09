from config import users


def cache(c_id):
    t = users.find_one({"cache_id": c_id})['auth']

    return t