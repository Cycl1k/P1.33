from telethon import TelegramClient, sync, events
from telethon.utils import get_display_name

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_qrcode import QRcode

import configparser
import asyncio

app = Flask(__name__)
qrcode = QRcode(app)

#Получаем данные из конфига
config = configparser.ConfigParser()
config.read('config.ini')

#Данные от Telegram API
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

#Генерация токена
@app.route('/login', methods = ['POST'])
def create_token():
    #Убираем ошибку потоков
    asyncio.set_event_loop(asyncio.new_event_loop()) 

    phone ='+' + request.json['phone'] 

    client = TelegramClient(phone, api_id, api_hash)
    client.connect()

    qr = client.qr_login()
    data = qr.url

    return jsonify({
        'qr_link_url': 'http://127.0.0.1:5000/qrcode?data=' + data
        })

#Генератор картинки с QR-кодом
@app.route("/qrcode", methods=["GET"])
def get_qrcode():
    # please get /qrcode?data=<qrcode_data>
    data = request.args.get("data", "")
    return send_file(qrcode(data, mode="raw"), mimetype="image/png")

#Отправка или возврат истории
@app.route('/message',methods = ["GET", "POST"])
def message_to_do():
    if request.method == 'POST':
        status = send_message()
        return jsonify({
            'status': status
        })
    else:
        messList = history_message()
        return jsonify({
            'messages': messList
        })

#Последнии 50 сообщений
def history_message(numberLimit=50):
    asyncio.set_event_loop(asyncio.new_event_loop())
    
    phone = '+' + request.args.get("phone","")
    uname = request.args.get("uname","")
    
    client = TelegramClient(phone, api_id, api_hash)
    client.connect()
    messList = []

    found_media = {}
    messages = client.get_messages(uname, limit=numberLimit)
    
    for msg in reversed(messages):
        name = get_display_name(msg.sender)

        #Тип сообщения
        if getattr(msg, 'media', None):
            found_media[msg.id] = msg
            content = '{}'.format(
                type(msg.media).__name__)

        elif hasattr(msg, 'message'):
            content = msg.message
        elif hasattr(msg, 'action'):
            content = str(msg.action)
        else:
            # В остальных случаях
            content = type(msg).__name__

        if str(msg.from_id) == 'None':
            isSelf = False
        else:
            isSelf = True

        messList.append(
            {
                'name': name,
                'is_self': isSelf,
                'message' : content
            }
        )
    
    client.disconnect()
    
    return messList

#Отправка сообщения
def send_message():
    asyncio.set_event_loop(asyncio.new_event_loop())

    message_text = request.json['message_text']
    phone = '+' + request.json['from_phone']
    username = request.json['username']

    client = TelegramClient(phone, api_id, api_hash)
    client.connect()

    try:
        client.send_message(username, message_text)
        client.disconnect()
        return 'ok'
    except ValueError:
        return 'error'
    except:
        return 'error'

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)