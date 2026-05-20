"""
Bloomberg Terminal Clone — Main Dash Application
Real-time NSE India dashboard.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

import os
from dotenv import load_dotenv
load_dotenv()

FAST_INTERVAL = int(os.getenv("INTERVAL_FAST", 1000))
MEDIUM_INTERVAL = int(os.getenv("INTERVAL_MEDIUM", 2000))
SLOW_INTERVAL = int(os.getenv("INTERVAL_SLOW", 15000))
# ── Components ───────────────────────────────
from components.topbar import create_topbar
from components.market_overview import create_market_overview
from components.price_chart import create_price_chart_panel, create_price_chart
from components.watchlist import create_watchlist_panel
from components.news_feed import create_news_panel
from components.market_stats import create_market_stats_panel

# ── Data ─────────────────────────────────────
from data.market_data import (
    generate_ticker_data,
    generate_index_data,
    generate_watchlist,
    generate_news_feed,
    generate_market_stats,
    generate_ohlc_data,
    start_data_cache,
    SECURITIES
)

# ── Callbacks ────────────────────────────────
from callbacks.realtime import register_callbacks


# ═════════════════════════════════════════════
# Initialize Dash App
# ═════════════════════════════════════════════

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="Bloomberg Terminal — NSE India",
    suppress_callback_exceptions=True,
)

server = app.server


# ═════════════════════════════════════════════
# START NSE DATA CACHE (IMPORTANT)
# ═════════════════════════════════════════════

start_data_cache(interval=10)


# ═════════════════════════════════════════════
# Generate Initial Data
# (Prevents blank dashboard on first load)
# ═════════════════════════════════════════════

try:
    ticker_data = generate_ticker_data()
except:
    ticker_data = []

try:
    index_data = generate_index_data()
except:
    index_data = []

try:
    watchlist_df = generate_watchlist()
except:
    watchlist_df = None

try:
    news_data = generate_news_feed(count=10)
except:
    news_data = []

try:
    market_stats = generate_market_stats()
except:
    market_stats = {}

try:
    ohlc_data = generate_ohlc_data("RELIANCE")
    initial_chart = create_price_chart(ohlc_data, "RELIANCE")
except:
    import plotly.graph_objects as go
    initial_chart = go.Figure()


# ═════════════════════════════════════════════
# Layout
# ═════════════════════════════════════════════

app.layout = html.Div(
    className="bloomberg-container",
    children=[

        # ── Interval Timers ──────────────────
        dcc.Interval(id="interval-fast", interval=FAST_INTERVAL, n_intervals=0),
        dcc.Interval(id="interval-medium", interval=MEDIUM_INTERVAL, n_intervals=0),
        dcc.Interval(id="interval-slow", interval=SLOW_INTERVAL, n_intervals=0),

        # ── Top Bar ──────────────────────────
        create_topbar(),

        # ── Market Overview ──────────────────
        create_market_overview(ticker_data, index_data),

        # ── Main Dashboard Grid ──────────────
        html.Div(
            className="dashboard-grid",
            children=[

                # Price Chart
                create_price_chart_panel(
                    initial_chart,
                    list(SECURITIES.keys())
                ),

                # News
                create_news_panel(news_data),

                # Watchlist
                create_watchlist_panel(watchlist_df),

                # Market Stats
                create_market_stats_panel(market_stats),
            ],
        ),
    ],
)


# ═════════════════════════════════════════════
# Register Callbacks
# ═════════════════════════════════════════════

register_callbacks(app)


# ═════════════════════════════════════════════
# Run Server
# ═════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)