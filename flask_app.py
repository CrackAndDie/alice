from flask import Flask, request
import logging
import json
import random
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1540737/daa6e420d33102bf6947',
               '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f',
                 '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8",
              '3450494/aca7ed7acefde22341bdc']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    if response['response'].get('buttons', 'gg') != 'gg':
        response['response']['buttons'].append({
                    'title': 'помощь',
                    'hide': True
                })
    else:
        response['response']['buttons'] = [{'title': 'помощь', 'hide': True}]
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет, назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return
    if 'помощь' not in req['request']['nlu']['tokens'] and "Покажи город на карте" not in req['request']['nlu']['tokens']:
        if sessionStorage[user_id]['first_name'] is None:
            first_name = get_first_name(req)
            if first_name is None:
                res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
            else:
                sessionStorage[user_id]['first_name'] = first_name
                sessionStorage[user_id]['guessed_cities'] = []
                res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я - Алиса, отгадаешь город по фото?'
                res['response']['buttons'] = [
                    {
                        'title': 'да',
                        'hide': True
                    },
                    {
                        'title': 'нет',
                        'hide': True
                    }
                ]
        else:
            if not sessionStorage[user_id]['game_started']:
                if 'да' in req['request']['nlu']['tokens']:
                    if len(sessionStorage[user_id]['guessed_cities']) == 3:
                        res['response']['text'] = 'Все города угаданы, спасибо за игру!'
                        res['end_session'] = True
                    else:
                        sessionStorage[user_id]['game_started'] = True
                        sessionStorage[user_id]['attempt'] = 1
                        play_game(res, req)
                elif 'нет' in req['request']['nlu']['tokens']:
                    res['response']['text'] = 'До свидания!'
                    res['end_session'] = True
                else:
                    res['response']['text'] = 'Не поняла ответа. Да или нет?'
                    res['response']['buttons'] = [
                        {
                            'title': 'да',
                            'hide': True
                        },
                        {
                            'title': 'нет',
                            'hide': True
                        }
                    ]
            else:
                play_game(res, req)
    else:
        res['response']['text'] = 'Это игра, где сначала нужно представиться, а потом попытаться угадать три города'


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Какой это город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Я угадал!'
    else:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            res['response']['text'] = 'Правильно. Сыграем еще?'
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            if res['response'].get('buttons', 'gg') != 'gg':
                res['response']['buttons'].append({
                    "title": "Покажи город на карте",
                    "url": "https://yandex.ru/maps/?mode=search&text={0}".format(city),
                    "hide": True
                })
            else:
                res['response']['buttons'] = [{
                    "title": "Покажи город на карте",
                    "url": "https://yandex.ru/maps/?mode=search&text={0}".format(city),
                    "hide": True
                }]
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем еще?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                if res['response'].get('buttons', 'gg') != 'gg':
                    res['response']['buttons'].append({
                        "title": "Покажи город на карте",
                        "url": "https://yandex.ru/maps/?mode=search&text={0}".format(city),
                        "hide": True
                    })
                else:
                    res['response']['buttons'] = [{
                        "title": "Покажи город на карте",
                        "url": "https://yandex.ru/maps/?mode=search&text={0}".format(city),
                        "hide": True
                    }]
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Не верно, попробуйте еще раз'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'Я угадал!'
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
