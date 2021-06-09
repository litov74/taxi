
def process_answer(data, answer):
    if data['status'] == 'success':
        return answer
    elif data['status'] == 'error':
        if 'message' in data:
            return {'error': f'Произошла ошибка: "{data["message"]}"'}
        else:
            return {'error': 'Произошла неизвестная ошибка'}
    else:
        return {'error': 'Произошла неизвестная ошибка'}