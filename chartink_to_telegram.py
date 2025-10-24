from flask import Flask, request, jsonify
import requests
import os
import time

# Optional: load .env during local dev if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; env vars can be set by the environment (recommended)
    pass

app = Flask(__name__)

# ------------------ CONFIG (from environment) ------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")               # production alerts
HEALTH_CHAT_ID = os.environ.get("HEALTH_CHAT_ID", CHAT_ID)  # health messages
PUBLIC_URL = os.environ.get("PUBLIC_URL")         # e.g. https://your-app.onrender.com
LOCAL_TEST = os.environ.get("LOCAL_TEST", "false").lower() in ("1","true","yes")
PORT = int(os.environ.get("PORT", 5000))
# --------------------------------------------------------------

if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
    # Stop early with clear error: token and chat id are required
    raise RuntimeError("TELEGRAM_BOT_TOKEN and CHAT_ID environment variables must be set. "
                       "Do NOT hardcode tokens in the code.")

def send_telegram_message(message, chat_id=CHAT_ID):
    """Send a message to Telegram. Returns (status_code, response_text)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return 500, str(e)


@app.route('/')
def home():
    return "✅ Telegram Bot Server is Live!"

@app.route('/health')
def health():
    """
    End-to-end health check (single summarized message).
    Behavior:
      - When PUBLIC_URL is set: test webhook against PUBLIC_URL + /chartink (remote full E2E)
      - If LOCAL_TEST is true: test webhook against localhost (for local dev)
      - Otherwise: skip webhook test (only test Telegram via getMe)
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    health_status = {"server": "up", "timestamp": ts, "telegram": "unknown", "webhook": "unknown"}

    # 1) Test Telegram bot validity via getMe (non-intrusive)
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=5)
        if r.status_code == 200 and r.json().get("ok"):
            health_status["telegram"] = "ok"
        else:
            health_status["telegram"] = f"error {r.status_code}"
    except Exception as e:
        health_status["telegram"] = f"exception: {str(e)}"

    # 2) Decide webhook test target
    webhook_result = None
    webhook_test_url = None
    dummy_payload = {
        "scan_name": "[Health Check] DummyScan",
        "symbol": "TEST",
        "close": "0"
    }

    if PUBLIC_URL:
        webhook_test_url = PUBLIC_URL.rstrip("/") + "/chartink"
    elif LOCAL_TEST:
        webhook_test_url = f"http://127.0.0.1:{PORT}/chartink"
    else:
        health_status["webhook"] = "skipped (no PUBLIC_URL and LOCAL_TEST not enabled)"

    # Perform webhook test if we have a URL
    if webhook_test_url:
        try:
            r = requests.post(webhook_test_url, json=dummy_payload, timeout=8)
            if r.status_code == 200:
                health_status["webhook"] = "ok"
            else:
                health_status["webhook"] = f"error {r.status_code}"
        except Exception as e:
            health_status["webhook"] = f"exception: {str(e)}"

    # 3) Send a single summarized message to health chat
    summary_message = (
        f"[Health Check] ⚡ Status at {ts}\n"
        f"Server: {health_status['server']}\n"
        f"Telegram: {health_status['telegram']}\n"
        f"Webhook: {health_status['webhook']}"
    )

    try:
        # We attempt to notify health chat, but don't crash if it fails
        send_telegram_message(summary_message, chat_id=HEALTH_CHAT_ID)
    except Exception as e:
        app.logger.exception("Failed to send health summary to Telegram: %s", e)

    return jsonify(health_status)


@app.route('/chartink', methods=['POST'])
def chartink_webhook():
    """
    Robust Chartink webhook: handles JSON or form-data, multiple key variations.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            data = request.form.to_dict()

        # Robust key handling
        scan_name = data.get("scan_name") or data.get("name") or "Unknown Scan"
        symbol = data.get("symbol") or data.get("stocks") or data.get("stock") or "Unknown Symbol"
        close = data.get("close") or data.get("price") or "Unknown Price"

        # Handle empty strings
        scan_name = scan_name if str(scan_name).strip() else "Unknown Scan"
        symbol = symbol if str(symbol).strip() else "Unknown Symbol"
        close = close if str(close).strip() else "Unknown Price"

        message = f"📈 {scan_name}\nSymbol: {symbol}\nClose: ₹{close}"

        status_code, response_text = send_telegram_message(message, chat_id=CHAT_ID)

        app.logger.info("Received payload: %s", data)
        app.logger.info("Telegram status: %s", status_code)

        return jsonify({"status": "Message sent", "telegram_status": status_code})

    except Exception as e:
        app.logger.exception("Webhook error")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)