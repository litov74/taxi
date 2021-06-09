def create_event(arr, bid, cache_id, code, n, prefix):
    from config import r, domain, delay
    from time import time

    event_id = f'{prefix}_{time()}_{bid}'
    expires = time() + 600
    r.hmset(f'event_{event_id}', {'bid': bid, 'cache_id': cache_id, 'code': code, 'expires': expires, 'n': n, 'prefix': prefix})

    arr['subscribe'] = f'{domain}/api/event/{event_id}'
    arr['delay'] = delay

    return arr