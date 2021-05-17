from flask import Flask, request
import requests
from yookassa import Configuration, Payment
from dotenv import load_dotenv
import json
import os
from os.path import join, dirname

app = Flask(__name__)


def create_invoice(chat_id):
    """ Отправляет ссылку на оплату"""
    Configuration.account_id = get_token("SHOP_ID")
    Configuration.secret_key = get_token("PAYMENT_TOKEN")

    payment = Payment.create({
        "amount": {
            "value": "100.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://www.google.com"
        },
        "capture": True,
        "description": "Заказ №1",
        "metadata": {"chat_id": chat_id}
    })

    return payment.confirmation.confirmation_url


def get_token(key):
    """ Возвращает ключи """
    token_path = join(dirname(__file__), '.env')
    load_dotenv(token_path)
    return os.environ.get(key)


def send_text(chat_id, text):
    """ Возвращает клиенту ответ """
    token = get_token("TELEGRAM_BOT_TOKEN")
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


def send_payment_button(chat_id, text):
    """ Возвращает клиенту кнопку оплаты"""
    invoice_url = create_invoice(chat_id)
    token = get_token("TELEGRAM_BOT_TOKEN")
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {"chat_id": chat_id, "text": text,
            "reply_markup": json.dumps({"inline_keyboard": [[{
                "text": "Оплатить!",
                "url": f"{invoice_url}"
            }]]})}

    requests.post(url, data=data)


def check_if_payment(request):
    """ Проверяет, успешно ли прошел платеж """
    try:
        if request.json["event"] == "payment.succeeded":
            return True
    except KeyError:
        return False

    return False


@app.route('/', methods=["POST"])
def process():
    if check_if_payment(request):
        """ Запрос от Юкассы """
        chat_id = request.json['object']['metadata']['chat_id']
        send_text(chat_id=chat_id, text="Оплата прошла успешно")
    else:
        """ Запрос от Телеграма"""
        chat_id = request.json['message']['chat']['id']
        send_payment_button(chat_id=chat_id, text="Оплата")

    return {"ok": True}


if __name__ == '__main__':
    app.run()
