from time import sleep, time


def create_action(arr, type, bid, cache_id, prefix):
    from config import r
    from config import domain

    arr['action'] = type
    action_id = f'{prefix}_{time()}_{bid}'
    action_url = f'{domain}/api/action/{action_id}'
    r.hmset(f'action_{action_id}', {'type': type, 'cache_id': cache_id, 'bid': bid, 'prefix': prefix})
    arr['action_url'] = action_url

    return arr