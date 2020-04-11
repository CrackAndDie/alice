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
counts = {'москва': 'россия', 'нью-йорк': 'сша', 'париж': 'франция'}

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
            'game_started': False,
            'talks': 1
        }
        return
    if 'помощь' not in req['request']['nlu']['tokens'] and "Покажи город на карте" != req['request']['command']:
        if sessionStorage[user_id]['first_name'] is None:
            first_name = get_first_name(req)
            if first_name is None:
                res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
            else:
                sessionStorage[user_id]['first_name'] = first_name
                sessionStorage[user_id]['guessed_cities'] = []
                res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я - Алиса, а из какого ты города?'
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
            if sessionStorage[user_id]['talks'] == 1:
                his_city = get_city(req)
                if his_city is None:
                    res['response']['text'] = 'Не расслышала город. Повтори, пожалуйста!'
                else:
                    sessionStorage[user_id]['guessed_cities'] = []
                    res['response'][
                        'text'] = f'О! Отличный город - {his_city.title()}. У меня есть игра, отгадаешь город по фото?'
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
                    sessionStorage[user_id]['talks'] = 0
            else:
                if not sessionStorage[user_id]['game_started']:
                    if 'да' in req['request']['nlu']['tokens']:
                        if len(sessionStorage[user_id]['guessed_cities']) == 3:
                            res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, все города угаданы, спасибо за игру!'
                            res['end_session'] = True
                        else:
                            sessionStorage[user_id]['game_started'] = True
                            sessionStorage[user_id]['attempt'] = 1
                            sessionStorage[user_id]['step'] = 1
                            play_game(res, req)
                    elif 'нет' in req['request']['nlu']['tokens']:
                        res['response']['text'] = f'До свидания, {sessionStorage[user_id]["first_name"]}!'
                        res['end_session'] = True
                    else:
                        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, не поняла ответа. Да или нет?'
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
    elif 'помощь' in req['request']['nlu']['tokens']:
        res['response']['text'] = 'Это игра, где сначала нужно представиться, а потом попытаться угадать три города'
    else:
        res['response']['text'] = 'Хорошо, сейчас покажу'


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    step = sessionStorage[user_id]['step']
    if step == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = f'{sessionStorage[user_id]["first_name"]}, какой это город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Я угадал!'
        sessionStorage[user_id]['step'] = 2
    elif step == 2:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            res['response']['text'] = f'Правильно. {sessionStorage[user_id]["first_name"]}, a в какой стране этот город?'
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = True
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
            sessionStorage[user_id]['step'] = 3
            sessionStorage[user_id]['attempt'] = 1
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Вы пытались. Это {city.title()}. А в какой стране этот город?'
                sessionStorage[user_id]['game_started'] = True
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
                sessionStorage[user_id]['step'] = 3
                sessionStorage[user_id]['attempt'] = 1
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = f'{sessionStorage[user_id]["first_name"]}, не верно, попробуйте еще раз'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'Я угадал!'
    elif step == 3:
        city = sessionStorage[user_id]['city']
        count = counts[city]
        if get_count(req) == count:
            res['response']['text'] = f'Правильно. {sessionStorage[user_id]["first_name"]}, cыграем еще?'
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
            sessionStorage[user_id]['step'] = 1
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Вы пытались. Это {count}. Сыграем еще?'
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
                sessionStorage[user_id]['step'] = 1
                return
            else:
                res['response']['text'] = f'Неверно! {sessionStorage[user_id]["first_name"]}, попробуйте еще раз'
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_count(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('country', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
