<div align="center">
  <h1>📊 Crypto Scanner Bot</h1>
  <p><strong>Async Telegram bot that scans 100+ crypto pairs, applies Smart Money Concepts analysis, and delivers actionable signals</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
  [![aiogram](https://img.shields.io/badge/aiogram-3.15-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://aiogram.dev)
  [![CCXT](https://img.shields.io/badge/CCXT-4.4-FF6B35?style=flat-square)](https://ccxt.com)
  [![pandas](https://img.shields.io/badge/pandas-2.2-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org)
  [![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
</div>

---

## What It Does

Crypto Scanner Bot continuously monitors cryptocurrency markets via the Binance API, applies a multi-layer technical analysis pipeline (Smart Money Concepts + classic indicators), and pushes real-time trading signals directly to users in Telegram.

Users receive structured signal cards with entry price, two take-profit targets, and a stop-loss — computed from order blocks, fair value gaps, and momentum indicators. A built-in paper trading engine lets users track virtual P&L without risking real capital.

---

## Signal Pipeline

```
Binance OHLCV (27 timeframes scanned)
          │
          ▼
  ┌───────────────────────────┐
  │  SMC Analysis             │
  │  ├─ Order Block detection │
  │  ├─ Fair Value Gap (FVG)  │
  │  ├─ Liquidity sweep       │
  │  └─ Break of Structure    │
  └──────────┬────────────────┘
             │
  ┌──────────▼────────────────┐
  │  Indicator Confluence     │
  │  ├─ RSI (14)              │
  │  ├─ MACD (12/26/9)        │
  │  ├─ EMA (20 / 50 / 200)   │
  │  ├─ Bollinger Bands       │
  │  └─ Volume delta          │
  └──────────┬────────────────┘
             │
  ┌──────────▼────────────────┐
  │  Scorer                   │
  │  Signal strength: 0–100   │
  │  Threshold filter > 65    │
  └──────────┬────────────────┘
             │
      Telegram signal card
  LONG BTC/USDT  │  Entry: $67,420
  TP1: $68,900   │  TP2: $70,200
  SL:  $66,100   │  R/R: 1:2.4
```

---

## Features

- **100+ pairs scanned** — all USDT pairs on Binance Spot, sorted by volume
- **Smart Money Concepts** — identifies institutional footprints (OB, FVG, BOS, liquidity grabs)
- **Multi-indicator confluence** — signal only fires when ≥ 3 indicators align
- **Paper trading engine** — virtual portfolio with real-time P&L, win rate, drawdown tracking
- **Per-user watchlists** — subscribe to specific pairs, get only relevant alerts
- **Web dashboard** — server-side HTML panel with scan statistics and signal history
- **Continuous scan loop** — runs as a background process, independent of the bot

---

## Quick Start

```bash
git clone https://github.com/daudbro73-collab/BOT.git
cd BOT
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# BOT_TOKEN=your_telegram_bot_token
# BINANCE_API_KEY=...   (optional — public endpoints work without it)

python main.py          # Telegram bot only
python scan_loop.py     # Bot + continuous market scanner
python dashboard.py     # Bot + web analytics panel
```

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and get usage guide |
| `/scan` | Trigger an on-demand market scan |
| `/signals` | Last 10 generated signals with outcomes |
| `/watchlist add BTCUSDT` | Subscribe to a specific pair |
| `/portfolio` | Virtual P&L, win rate, open positions |
| `/stats` | Global bot statistics |

---

## Architecture

```
BOT/
├── main.py                 # aiogram entry point, dispatcher setup
├── config.py               # Pydantic Settings from .env
├── scan_loop.py            # Independent scanner process
├── dashboard.py            # aiohttp web dashboard server
└── src/
    ├── bot/
    │   ├── handlers.py     # All command + callback handlers
    │   └── formatting.py   # Signal card HTML formatter
    ├── scanner/
    │   └── engine.py       # Main scan orchestrator
    ├── analysis/
    │   ├── smc.py          # Smart Money Concepts logic
    │   ├── indicators.py   # RSI, MACD, EMA, BB wrappers
    │   └── scorer.py       # Confluence scoring (0–100)
    ├── exchange/
    │   ├── binance.py      # Async CCXT Binance client
    │   └── screener.py     # Volume-ranked pair screener
    ├── trading/
    │   └── paper_trader.py # Virtual portfolio manager
    └── storage/
        └── users.py        # JSON-backed user store
```

---

## Tech Stack

| | Technology | Purpose |
|-|------------|---------|
| 🤖 | aiogram 3.15 | Async Telegram Bot framework |
| 📡 | CCXT 4.4 | Unified exchange API (Binance) |
| 📊 | pandas 2.2 + numpy | OHLCV data manipulation |
| 📈 | ta library | 50+ technical indicators |
| ✅ | pydantic v2 | Settings validation |
| 🌐 | aiohttp | Async HTTP (dashboard server) |

---

<div align="center">
  <strong>Built by Rustam Berheev</strong><br/>
  <a href="https://github.com/daudbro73-collab">github.com/daudbro73-collab</a>
</div>
