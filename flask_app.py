from flask import Flask, request
import logging
import json
import random
import os
import requests

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
        res['response']['text'] = 'Привет, чем могу помочь?'
        sessionStorage[user_id] = {
            'first_name': None,
            'first_name_up': None,
            'game_started': False,
            'talks': 1
        }
        return
    if 'помощь' not in req['request']['nlu']['tokens']:
        toks = [i.lower() for i in req['request']['nlu']['tokens']]
        f1 = 'переведи' in toks
        f2 = 'переведите' in toks
        f3 = 'слово' in toks
        if (f1 or f2) and f3:
            toks.remove('слово')
            if f1:
                toks.remove('переведи')
            else:
                toks.remove('переведите')
            if len(toks) == 0:
                res['response']['text'] = 'Не поняла, какое слово переводить. Повтори, пожалуйста!'
            else:
                tr = get_translate(' '.join(toks))['text'][0]
                res['response']['text'] = tr
        else:
            res['response']['text'] = 'Не поняла, что нужно сделать. Повтори, пожалуйста!'
    elif 'помощь' in req['request']['nlu']['tokens']:
        res['response']['text'] = 'Это игра, где сначала нужно представиться, а потом попытаться угадать три города'


def get_translate(st: str):
    try:
        req = 'https://translate.yandex.net/api/v1.5/tr.json/detect'
        params = {
            "key": "trnsl.1.1.20200411T113803Z.f661d69aa693eb4c.d99aa52bc5efc6f58fb380cd99cdfca38ead73d7",
            "text": st,
            'hint': ['en', 'ru']
        }
        response = requests.get(req, params=params)
        json_response = response.json()
        if json_response['lang'] == 'en':
            req = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
            geocoder_params = {
                "key": "trnsl.1.1.20200411T113803Z.f661d69aa693eb4c.d99aa52bc5efc6f58fb380cd99cdfca38ead73d7",
                "text": st,
                "lang": 'ru'}
            response = requests.get(req, params=geocoder_params)
            json_response = response.json()
            return json_response
        else:
            req = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
            geocoder_params = {
                "key": "trnsl.1.1.20200411T113803Z.f661d69aa693eb4c.d99aa52bc5efc6f58fb380cd99cdfca38ead73d7",
                "text": st,
                "lang": 'en'}
            response = requests.get(req, params=geocoder_params)
            json_response = response.json()
            return json_response
    except (Exception, KeyError):
        return None


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
