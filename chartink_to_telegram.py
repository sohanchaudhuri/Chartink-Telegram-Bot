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

    screener = data.get('scan_name', 'Unknown')
    symbol = data.get('symbol', 'N/A')
    price = data.get('close', 'N/A')

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