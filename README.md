# 📈 NSE India Stock Intelligence Platform

A Bloomberg Terminal-style real-time dashboard and NSE data pipeline built for the Indian stock market.

---

## 🎯 Project Objective

The goal of this project is to build a **self-hosted, real-time NSE India stock intelligence system** that combines:

1. **A data pipeline** (`stock.py` + `NSE/`) — Fetches, parses, and stores corporate disclosures, announcements, board meetings, insider trading data, historical OHLC data, and more from NSE India's API endpoints. All data is saved as JSON and optionally persisted to a SQL database.

2. **A Bloomberg Terminal-style dashboard** (`antigravity/`) — A live, interactive web dashboard built with Plotly Dash that displays real-time price tickers, index levels, candlestick charts, news feeds, and market stats — all driven by the live NSE data pipeline.

The system is designed to be **fully local**, with no paid data subscriptions, giving you institutional-grade market visibility at zero cost.

---

## 📁 Project Structure

```
stock2_fetcher/
│
├── antigravity/                # 🖥️  Bloomberg-style Dash Dashboard
│   ├── app.py                  #     Main entry point — run this to launch
│   ├── requirements.txt        #     Python dependencies
│   ├── components/             #     UI components (topbar, charts, watchlist, news, stats)
│   ├── callbacks/              #     Real-time Dash callbacks (live data updates)
│   ├── data/                   #     Data layer — fetches & caches NSE market data
│   ├── assets/                 #     Static CSS / JS assets
│   └── json_data/              #     Cached JSON snapshots from NSE
│
├── NSE/                        # 🔌  NSE Data Fetcher Package
│   ├── nse_data_fetcher/       #     Core fetcher module
│   │   ├── fetcher.py          #     Corporate_Announcements class (main API interface)
│   │   ├── db_operations.py    #     SQL database persistence layer
│   │   ├── save_attachment.py  #     PDF/attachment downloader for annual reports
│   │   └── utils.py            #     Decorators: @fetch_data, @track_time
│   └── setup.py                #     Package installer
│
├── stock.py                    # 🧪  Standalone script / quick data fetch utility
├── .env                        # 🔑  Environment config (intervals, API keys)
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/your-username/stock2-fetcher.git
cd stock2-fetcher
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r antigravity/requirements.txt
pip install -e NSE/           # Install NSE fetcher package
```

### 4. Configure environment
Copy and edit `.env` as needed:
```env
INTERVAL_FAST=1000       # ms — ticker refresh rate
INTERVAL_MEDIUM=2000     # ms — chart refresh rate
INTERVAL_SLOW=15000      # ms — news/stats refresh rate
```

### 5. Run the Dashboard
```bash
cd antigravity
python app.py
```
Open your browser at: **http://localhost:8000**

---

## 🖥️ Dashboard Features (`antigravity/`)

| Feature | Description |
|---|---|
| **Live Ticker Bar** | Real-time NSE stock prices scrolling across the top |
| **Index Overview** | NIFTY 50, SENSEX, NIFTY BANK live levels |
| **Candlestick Chart** | Interactive OHLC chart with stock selector |
| **Watchlist** | Sortable table of tracked securities with P&L |
| **News Feed** | Live NSE RSS feed with corporate announcements |
| **Market Stats** | Advances/Declines, 52W H/L, volume, volatility |
| **Auto-refresh** | All panels update automatically via interval timers |

**Theme:** Bloomberg-dark (Plotly CYBORG + custom CSS)

---

## 🔌 NSE Data Fetcher (`NSE/` & `stock.py`)

The `Corperate_Announcements` class in `stock.py` / `NSE/nse_data_fetcher/fetcher.py` provides:

| Method | Data |
|---|---|
| `get_corporate_announcements()` | Corporate disclosures |
| `get_annual_reports()` | Annual report PDFs |
| `get_board_meetings()` | Board meeting schedules |
| `get_financial_results()` | Quarterly P&L results |
| `get_insider_trading()` | SAST / insider trade filings |
| `get_buybacks()` | Buyback program data |
| `get_historical_data()` | OHLCV data (auto-paginated) |
| `get_rss_feed()` | NSE live RSS news feed |

All methods:
- Auto-build NSE API URLs via `@fetch_data` decorator
- Record timestamps via `@track_time` decorator
- Save raw output as JSON to `json_data/`
- Optionally persist to SQL via `DatabaseHandler`

---

## 🛣️ Current Stage

> **Stage: Active Development — MVP Dashboard Live**

- ✅ NSE data fetcher pipeline is functional
- ✅ Bloomberg-style Dash dashboard is running
- ✅ Real-time intervals wired up (fast / medium / slow)
- ✅ Price chart, watchlist, news, market stats panels complete
- ✅ Modular component + callback architecture
- ✅ JSON caching for offline / fallback use
- ✅ Project structure cleaned and organized

---

## 📋 TODO

- [ ] Fetch all NSE-listed companies instead of only the hardcoded ones
- [ ] Integrate AI agents

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Dashboard UI | [Plotly Dash](https://dash.plotly.com/) + Dash Bootstrap Components |
| Charts | [Plotly](https://plotly.com/python/) |
| Data Fetching | `requests`, `feedparser`, custom NSE decorators |
| Data Processing | `pandas`, `numpy` |
| Database | SQLAlchemy (SQLite / PostgreSQL) |
| Config | `python-dotenv` |
| Packaging | `setuptools` (NSE package) |

---

## ⚠️ Disclaimer

This project fetches publicly available data from NSE India's web endpoints. It is intended for **personal research and educational use only**. Not financial advice. Always verify data with official NSE sources before making investment decisions.

---

## 📄 License

MIT License — free to use, modify, and distribute.
