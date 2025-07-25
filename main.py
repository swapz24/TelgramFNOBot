
import time
import requests
import yfinance as yf
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from flask import Flask, request
import json
import os

# --- Telegram Setup ---
BOT_TOKEN = "7993502945:AAHdgPtK643W4YW4GkX1tvDi6NLD92jPCKc"
CHAT_ID = "274946332"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
app = Flask(__name__)

WATCHLIST_FILE = "watchlist.json"
def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return {
        "BAJFINANCE": "BAJFINANCE.NS", "TCS": "TCS.NS"
    }

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f)

equities = load_watchlist()

def send_telegram_alert(message):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", data=payload)
    except Exception as e:
        print("Error sending message:", e)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        msg_text = data["message"]["text"].lower().strip()
        user_text = data["message"]["text"].strip()
        command_parts = user_text.split()

        if "/check" in msg_text:
            send_telegram_alert("✅ Check command received.")
        elif "/summary" in msg_text:
            send_telegram_alert("📊 Evening summary triggered.")
        elif "/start" in msg_text or "/help" in msg_text:
            help_message = (
                "👋 *Welcome to the Market Alert Bot!*"     
                "Available commands:"
                "/check – Run a live signal check"
                "/summary – Get today's evening summary"
                "/list – View current watchlist"
                "/add SYMBOL – Add stock/index (e.g. /add RELIANCE)"
                "/remove SYMBOL – Remove stock/index (e.g. /remove TCS)"
                "/start or /help – Show this help message"
            )
            send_telegram_alert(help_message)
        elif "/list" in msg_text:
            stock_list = ', '.join(equities.keys())
            send_telegram_alert(f"📋 *Current Watchlist:*{stock_list}")
        elif "/add" in msg_text and len(command_parts) == 2:
            symbol = command_parts[1].upper()
            equities[symbol] = f"{symbol}.NS"
            save_watchlist(equities)
            send_telegram_alert(f"✅ Added {symbol} to watchlist.")
        elif "/remove" in msg_text and len(command_parts) == 2:
            symbol = command_parts[1].upper()
            if symbol in equities:
                equities.pop(symbol)
                save_watchlist(equities)
                send_telegram_alert(f"❌ Removed {symbol} from watchlist.")
            else:
                send_telegram_alert(f"⚠️ Symbol {symbol} not found in watchlist.")
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
