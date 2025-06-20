from flask import Flask, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'  # вставь сюда свой токен
CHAT_ID = 651911888    # вставь сюда свой Telegram ID

def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

@app.route("/send_location", methods=["POST"])
def send_location():
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat and lon:
        send_to_telegram(lat, lon)
        return {"status": "ok"}
    return {"status": "error"}, 400

@app.route("/")
def home():
    return "👋 Сервер работает!"

if __name__ == "__main__":
    app.run()
