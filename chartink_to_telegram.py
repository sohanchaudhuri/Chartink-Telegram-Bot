from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# ------------------ CONFIG ------------------
TELEGRAM_BOT_TOKEN = "7857280968:AAG6rFmqSo6tTlUm-RqY5IBKgEn2BlCOIVI"
CHAT_ID = "1380193077"              # Production chat for real alerts
HEALTH_CHAT_ID = "1380193077"           # Health check messages sent here (can be same as private chat)
# -------------------------------------------

@app.route('/')
def home():
    """Simple server live check"""
    return "✅ Telegram Bot Server is Live!"

@app.route('/health')
def health():
    """
    End-to-end health check with a single summarized message.
    Checks:
    - Server is up
    - Telegram bot connectivity
    - Webhook endpoint functioning
    """
    health_status = {
        "server": "up",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "telegram": "unknown",
        "webhook": "unknown"
    }

    ts = health_status["timestamp"]

    # 1️⃣ Check Telegram bot connectivity
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.json().get("ok"):
            health_status["telegram"] = "ok"
        else:
            health_status["telegram"] = f"error {response.status_code}"
    except Exception as e:
        health_status["telegram"] = f"exception: {str(e)}"

    # 2️⃣ Check webhook endpoint locally with dummy payload
    try:
        dummy_payload = {
            "scan_name": "[Health Check] DummyScan",
            "symbol": "TEST",
            "close": "0"
        }
        webhook_url = f"http://127.0.0.1:{os.environ.get('PORT',5000)}/chartink"
        response = requests.post(webhook_url, json=dummy_payload, timeout=5)
        if response.status_code == 200:
            health_status["webhook"] = "ok"
        else:
            health_status["webhook"] = f"error {response.status_code}"
    except Exception as e:
        health_status["webhook"] = f"exception: {str(e)}"

    # 3️⃣ Send single summarized health message to health chat
    summary_message = (
        f"[Health Check] ⚡ Status at {ts}\n"
        f"Server: {health_status['server']}\n"
        f"Telegram: {health_status['telegram']}\n"
        f"Webhook: {health_status['webhook']}"
    )

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": HEALTH_CHAT_ID, "text": summary_message}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram exception while sending summary:", str(e))

    return jsonify(health_status)

def send_telegram_message(message, chat_id=CHAT_ID):
    """
    Send a message to Telegram.
    By default, sends to production chat unless overridden (e.g., for health check)
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print("Telegram send error:", response.text)
        return response.status_code, response.text
    except Exception as e:
        print("Telegram exception:", str(e))
        return 500, str(e)

@app.route('/chartink', methods=['POST'])
def chartink_webhook():
    """
    Main webhook for Chartink alerts
    """
    try:
        # Parse JSON or fallback to form-data
        data = request.get_json(force=True, silent=True)
        if not data:
            data = request.form.to_dict()

        # Extract fields
        scan_name = data.get("scan_name") or data.get("name") or "Unknown Scan"
        symbol = data.get("symbol") or data.get("stocks") or data.get("stock") or "Unknown Symbol"
        close = data.get("close") or data.get("price") or "Unknown Price"

        # Build message
        message = f"📈 {scan_name}\nSymbol: {symbol}\nClose: ₹{close}"

        # Send to Telegram
        status_code, response_text = send_telegram_message(message)

        print("Received payload:", data)
        print(f"Telegram status: {status_code}, response: {response_text}")

        return jsonify({"status": "Message sent", "telegram_status": status_code})

    except Exception as e:
        print("Webhook error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
