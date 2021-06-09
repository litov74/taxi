def check_token(token, prefix):
    from config import tokens

    res = tokens.find_one({'token': token})
    if res:
        if res['prefix'] == prefix:
            return True

    return False