from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔹 Your Telegram Bot details
BOT_TOKEN = "8422561933:AAEsghs2BiSmB0WuCMsZ3xzL5_2otIpDdyc"
CHAT_ID = "1357033271"

@app.route('/chartink', methods=['POST'])
def chartink_alert():
    data = request.json
    print("Received:", data)

    # Chartink may send different keys depending on alert type
    screener = data.get('scan_name', 'Unknown Screener')
    symbol = None
    price = None

    # When default Chartink webhook format is used
    if "stocks" in data and len(data["stocks"]) > 0:
        symbol = data["stocks"][0].get("n", "N/A")
        price = data["stocks"][0].get("b", "N/A")

    message = f"🚨 *Chartink Alert!*\n📊 *Screener:* {screener}\n💹 *Symbol:* {symbol}\n💰 *Price:* {price}"
    send_message(message)
    return {"status": "ok"}


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)