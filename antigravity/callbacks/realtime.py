"""
Real-time Callbacks — dcc.Interval-driven updates for all dashboard panels.
Updated for live NSE India data with ₹ (INR) formatting.
"""

from dash import Input, Output, html
from datetime import datetime
import pandas as pd

from data.market_data import (
    generate_ticker_data,
    generate_ohlc_data,
    generate_index_data,
    generate_watchlist,
    generate_news_feed,
    generate_market_stats,
)

from components.price_chart import create_price_chart
from components.news_feed import create_news_item


def register_callbacks(app):

    # ── Clock update ─────────────────────────
    @app.callback(
        Output("topbar-clock", "children"),
        Input("interval-fast", "n_intervals"),
    )
    def update_clock(_):
        return datetime.now().strftime("%H:%M:%S")



    # ── Ticker tape update ───────────────────
    @app.callback(
        Output("ticker-tape", "children"),
        Input("interval-medium", "n_intervals"),
    )
    def update_ticker_tape(_):

        ticker_data = generate_ticker_data()

        if not ticker_data:
            return []

        items = []

        for t in ticker_data:

            change_class = (
                "ticker-change-up" if t["change"] >= 0 else "ticker-change-down"
            )

            arrow = "▲" if t["change"] >= 0 else "▼"
            sign = "+" if t["change"] >= 0 else ""

            items.append(
                html.Div(
                    className="ticker-item",
                    children=[
                        html.Span(t["symbol"], className="ticker-symbol"),
                        html.Span(f"₹{t['price']:,.2f}", className="ticker-price"),
                        html.Span(
                            f"{arrow} {sign}{t['change_pct']:.2f}%",
                            className=change_class,
                        ),
                        html.Span("│", className="ticker-divider"),
                    ],
                )
            )

        return items + items



    # ── Index cards update ───────────────────
    @app.callback(
        Output("index-cards", "children"),
        Input("interval-medium", "n_intervals"),
    )
    def update_index_cards(_):

        index_data = generate_index_data()

        if not index_data:
            return []

        cards = []

        for idx in index_data:

            change_class = "change-positive" if idx["change"] >= 0 else "change-negative"
            sign = "+" if idx["change"] >= 0 else ""
            arrow = "▲" if idx["change"] >= 0 else "▼"

            cards.append(
                html.Div(
                    className="index-card",
                    children=[
                        html.Div(idx["name"], className="index-card-name"),
                        html.Div(f"{idx['value']:,.2f}", className="index-card-value"),
                        html.Div(
                            f"{arrow} {sign}{idx['change']:.2f} ({sign}{idx['change_pct']:.2f}%)",
                            className=f"index-card-change {change_class}",
                        ),
                    ],
                )
            )

        return cards



    # ── Price chart update ───────────────────
    # ── Price chart update ───────────────────
    @app.callback(
        Output("price-chart", "figure"),
        Output("ohlc-open", "children"),
        Output("ohlc-high", "children"),
        Output("ohlc-low", "children"),
        Output("ohlc-close", "children"),
        [
            Input("interval-slow", "n_intervals"),
            Input("chart-symbol-dropdown", "value"),
        ],
    )
    def update_price_chart(_, symbol):

        if not symbol:
            symbol = "RELIANCE"

        try:

            df = generate_ohlc_data(symbol, days=30)

            if df is None or df.empty:
                fig = create_price_chart(pd.DataFrame(), symbol)
                return fig, "-", "-", "-", "-"

        # moving averages
            df["sma20"] = df["close"].rolling(20).mean()
            df["sma50"] = df["close"].rolling(50).mean()

            fig = create_price_chart(df, symbol)

            last = df.iloc[-1]

            open_price = f"{last['open']:,.2f}"
            high_price = f"{last['high']:,.2f}"
            low_price = f"{last['low']:,.2f}"
            close_price = f"{last['close']:,.2f}"

            return fig, open_price, high_price, low_price, close_price

        except Exception as e:

            print("Chart callback error:", e)

            fig = create_price_chart(pd.DataFrame(), symbol)

            return fig, "-", "-", "-", "-"


    # ── Watchlist update ─────────────────────
    @app.callback(
        Output("watchlist-table", "data"),
        Input("interval-medium", "n_intervals"),
    )
    def update_watchlist(_):

        df = generate_watchlist()

        if df is None or df.empty:
            return []

        return df.to_dict("records")



    # ── News feed update ─────────────────────
    @app.callback(
        Output("news-feed-body", "children"),
        Input("interval-slow", "n_intervals"),
    )
    def update_news_feed(_):

        news_data = generate_news_feed(count=10)

        if not news_data:
            return [
                html.Div(
                    "No news available",
                    style={"color": "#777", "padding": "15px"},
                )
            ]

        items = []

        for n in news_data:

            try:

                items.append(
                    create_news_item(
                        {
                            "timestamp": n.get("timestamp", "--:--"),
                            "headline": n.get("headline", "NSE update"),
                            "source": n.get("source", "NSE"),
                            "category": n.get("category", "INFO"),
                        }
                    )
                )

            except Exception as e:

                print("News item error:", e)

        return items



    # ── Market stats update ──────────────────
    @app.callback(
        Output("market-stats-body", "children"),
        Input("interval-medium", "n_intervals"),
    )
    def update_market_stats(_):

        stats = generate_market_stats()

        if not stats:
            return []

        from components.market_stats import create_stat_card, _safe_fmt

        cards = [

            create_stat_card("India VIX", stats.get("india_vix", "N/A")),

            create_stat_card(
                "Bank NIFTY",
                _safe_fmt(stats.get("bank_nifty", "N/A"), "{0:,.2f}"),
            ),

            create_stat_card("Adv/Decl", stats.get("adv_decl", "N/A")),

            create_stat_card(
                "USD/INR",
                _safe_fmt(stats.get("usd_inr", "N/A"), "{0:.2f}", prefix="₹"),
            ),

            create_stat_card(
                "Gold MCX",
                _safe_fmt(stats.get("gold_mcx", "N/A"), "{0:,.0f}", prefix="₹"),
            ),

            create_stat_card(
                "Crude MCX",
                _safe_fmt(stats.get("crude_mcx", "N/A"), "{0:,.0f}", prefix="₹"),
            ),

            create_stat_card("Put/Call", stats.get("put_call", "N/A")),

            create_stat_card("FII/DII", stats.get("fii_dii", "N/A")),

            create_stat_card("Turnover", stats.get("mkt_turnover", "N/A")),

            create_stat_card("New Highs", stats.get("new_highs", "N/A")),

            create_stat_card("52W Highs", stats.get("new_highs", "N/A")),
        ]

        return [html.Div(className="stats-grid", children=cards)]