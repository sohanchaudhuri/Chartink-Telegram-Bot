from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ------------------ CONFIG ------------------
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
# -------------------------------------------

def send_telegram_message(message):
    """Send a message to your Telegram chat using bot token"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
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
    try:
        # Try to parse JSON first
        data = request.get_json(force=True, silent=True)

        # Fallback to form-data if JSON is empty
        if not data:
            data = request.form.to_dict()

        # Extract relevant fields
        scan_name = data.get("scan_name") or data.get("name") or "Unknown Scan"
        symbol = data.get("symbol") or data.get("stocks") or data.get("stock") or "Unknown Symbol"
        close = data.get("close") or data.get("price") or "Unknown Price"

        # Construct message
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