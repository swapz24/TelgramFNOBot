# FNO Trading Bot (Telegram + GPT Signal Assistant)

This bot scans Indian F&O stocks for intraday/scalping opportunities using:
- RSI, MACD, VWAP, Bollinger Bands
- Live signal generation with CE/PE strike suggestion (based on OI, IV, expiry)
- Telegram integration for alerts & commands
- Scheduled 30-min scans + 3:15 PM daily summary

## 🚀 Deployment (Docker)

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
docker build -t fnobot .
docker run -d -p 5000:5000 fnobot
```

Edit `main_updated.py` with your Telegram `BOT_TOKEN` and `CHAT_ID`.

## 🧠 GPT Prompt Ideas

- Scan Nifty stocks for RSI<30 + MACD cross
- Suggest CE/PE for expiry week based on IV/OI
- Build scalping strategy using VWAP + Bollinger Band
