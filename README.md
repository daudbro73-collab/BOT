<div align="center">

# 📊 Crypto Scanner Bot

**AI-powered Telegram bot for crypto market scanning, signals and paper trading**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.15-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://aiogram.dev)
[![CCXT](https://img.shields.io/badge/CCXT-4.4-FF6B35?style=for-the-badge)](https://ccxt.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

[🤖 Try on Telegram](#) · [📖 Documentation](#)

</div>

---

## 📋 Overview

**Crypto Scanner Bot** is a Telegram bot that continuously scans cryptocurrency markets using technical analysis, detects high-probability trading setups based on Smart Money Concepts (SMC), and delivers real-time signals with entry, take-profit, and stop-loss levels directly in Telegram.

---

## ✨ Features

- 📡 **Real-time market scanning** — monitors 100+ crypto pairs on Binance
- 🧠 **Smart Money Concepts (SMC)** — order blocks, fair value gaps, liquidity sweeps
- 📈 **Multi-indicator scoring** — RSI, MACD, EMA, Bollinger Bands, volume
- 🎯 **Signal generation** — LONG/SHORT setups with Entry, TP1, TP2, SL
- 📊 **Paper trading** — track virtual P&L without real money
- 👥 **User management** — per-user watchlists and preferences
- 📉 **Web dashboard** — interactive analytics panel

---

## 🚀 Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/daudbro73-collab/BOT.git
cd BOT
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# BOT_TOKEN=your_telegram_bot_token
# BINANCE_API_KEY=your_key      # optional
# BINANCE_SECRET=your_secret    # optional
```

### 3. Run

```bash
python main.py          # Bot only
python scan_loop.py     # Bot + continuous scanner
python dashboard.py     # Bot + web dashboard
```

---

## 📡 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome & registration |
| `/scan` | Manual market scan |
| `/signals` | Latest trading signals |
| `/watchlist` | Manage pairs |
| `/portfolio` | Paper trading P&L |
| `/stats` | Bot statistics |

---

## 🔬 Analysis Engine

### Smart Money Concepts (SMC)
- **Order Blocks** — institutional buy/sell zones
- **Fair Value Gaps (FVG)** — imbalance detection
- **Liquidity Sweeps** — stop-hunt pattern recognition
- **Break of Structure (BOS)** — trend change confirmation

### Technical Indicators
- RSI (14), MACD (12,26,9), EMA (20/50/200), Bollinger Bands, Volume

---

## 🏗️ Project Structure

```
BOT/
├── main.py                 # Bot entry point
├── config.py               # Settings (env-driven)
├── scan_loop.py            # Continuous scanner
├── dashboard.py            # Web dashboard
└── src/
    ├── bot/                # Telegram handlers & formatting
    ├── scanner/            # Market scanning engine
    ├── analysis/           # SMC, indicators, scorer
    ├── exchange/           # Binance API + screener
    ├── trading/            # Paper trading engine
    ├── storage/            # User data store
    └── dashboard/          # Web UI
```

---

## 💡 Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot | aiogram 3.15 (async) |
| Exchange | CCXT 4.4 (Binance) |
| Data | pandas, numpy |
| TA | ta (Technical Analysis library) |
| Validation | pydantic + pydantic-settings |
| HTTP | aiohttp |

---

<div align="center">

Built with ❤️ by **Rustam Berheev**

[![GitHub](https://img.shields.io/badge/GitHub-daudbro73--collab-181717?style=flat-square&logo=github)](https://github.com/daudbro73-collab)

</div>
