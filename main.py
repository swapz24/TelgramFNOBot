
import requests
import yfinance as yf
import pandas as pd
from flask import Flask, request
import datetime as dt
import json
import os
import threading
import time
import schedule
import pytz

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange

app = Flask(__name__)

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_alert(message):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", data=payload)
    except Exception as e:
        print("Telegram Error:", e)

def calculate_supertrend(df, period=10, multiplier=3):
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=period).average_true_range()
    hl2 = (df['High'] + df['Low']) / 2
    df['UpperBand'] = hl2 + (multiplier * atr)
    df['LowerBand'] = hl2 - (multiplier * atr)
    df['Supertrend'] = df['Close'] > df['UpperBand']
    return df

def run_full_scan_and_suggest():
    fno_stocks = [
        "SBIN", "ASIANPAINT", "TATAMOTORS", "RELIANCE", "ICICIBANK",
        "INFY", "TCS", "AXISBANK", "HDFCBANK", "KOTAKBANK", "BAJFINANCE",
        "MARUTI", "ONGC", "POWERGRID", "ITC", "ULTRACEMCO", "LT", "HINDUNILVR",
        "WIPRO", "TECHM", "DIVISLAB", "ADANIENT", "COALINDIA", "CIPLA", "HCLTECH"
    ]
    suggestions = []
    for symbol in fno_stocks:
        try:
            df = yf.download(f"{symbol}.NS", period="5d", interval="15m")
            if df.empty:
                continue
            df['RSI'] = RSIIndicator(df['Close']).rsi()
            macd = MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            df['EMA20'] = EMAIndicator(df['Close'], window=20).ema_indicator()
            df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
            bb = BollingerBands(df['Close'])
            df['BBH'] = bb.bollinger_hband()
            df['BBL'] = bb.bollinger_lband()
            df = calculate_supertrend(df)

            latest = df.iloc[-1]
            score = 0
            signal = []
            trend = 'bullish' if latest['Close'] > latest['VWAP'] else 'bearish'
            if latest['RSI'] < 35: score += 1; signal.append("RSI < 35")
            if latest['RSI'] > 70: score += 1; signal.append("RSI > 70")
            if latest['MACD'] > latest['MACD_signal']: score += 1; signal.append("MACD Bullish")
            if latest['MACD'] < latest['MACD_signal']: score += 1; signal.append("MACD Bearish")
            if latest['Close'] > latest['BBH']: score += 1; signal.append("Above BB High")
            if latest['Close'] < latest['BBL']: score += 1; signal.append("Below BB Low")
            if latest['Close'] > latest['VWAP']: score += 1; signal.append("Above VWAP")
            if latest['Close'] < latest['VWAP']: score += 1; signal.append("Below VWAP")
            if latest['Supertrend']: score += 1; signal.append("Supertrend Bullish")
            if not latest['Supertrend']: score += 1; signal.append("Supertrend Bearish")

            strike = round(latest['Close'] / 50) * 50
            direction = f"Buy {strike}CE" if trend == "bullish" else f"Buy {strike}PE"
            suggestions.append((score, symbol, direction, ", ".join(signal)))
        except Exception as e:
            print(symbol, "error:", e)

    top = sorted(suggestions, key=lambda x: -x[0])[:10]
    message = "📊 *Top CE/PE Trades Scan* (Live)\n"
    for i, (score, sym, idea, why) in enumerate(top, 1):
        message += f"\n{i}. {sym} – *{idea}* ({why})"
    send_telegram_alert(message)

def send_evening_summary():
    now = dt.datetime.now(pytz.timezone("Asia/Kolkata"))
    message = f"📉 *Evening Summary - {now.strftime('%d-%b %a')}*\n"
    message += "\nScan complete for key stocks. Review top moves and Finviz charts:"
    links = [
        "https://finviz.com/quote.ashx?t=RELIANCE",
        "https://finviz.com/quote.ashx?t=TCS",
        "https://finviz.com/quote.ashx?t=SBIN",
        "https://finviz.com/quote.ashx?t=ICICIBANK"
    ]
    for link in links:
        message += f"\n📊 {link}"
    send_telegram_alert(message)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        msg = data["message"]["text"].lower()
        if "/summary" in msg:
            send_evening_summary()
            send_telegram_alert("📬 Summary sent.")
        elif "/scanall" in msg:
            run_full_scan_and_suggest()
            send_telegram_alert("✅ Scan triggered successfully.")
    return {"status": "ok"}, 200

def start_scheduler():
    schedule.every().day.at("15:15").do(send_evening_summary)
    schedule.every(30).minutes.do(run_full_scan_and_suggest)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=start_scheduler).start()
    app.run(host="0.0.0.0", port=5000)
