"""
Price Chart Component — Candlestick chart with volume and moving averages.
"""

from dash import html, dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots


CHART_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='#141428',
    plot_bgcolor='#0f0f23',
    font=dict(family='JetBrains Mono, SF Mono, Consolas, monospace', size=10, color='#e8e8f0'),
    margin=dict(l=50, r=20, t=10, b=30),
    xaxis_rangeslider_visible=False,
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1,
        font=dict(size=9, color='#8888aa'),
        bgcolor='rgba(0,0,0,0)',
    ),
    xaxis=dict(
        gridcolor='#1e1e35',
        linecolor='#2a2a4a',
        tickfont=dict(size=9),
    ),
    yaxis=dict(
        gridcolor='#1e1e35',
        linecolor='#2a2a4a',
        tickfont=dict(size=9),
        side='right',
    ),
)


def create_price_chart(df, symbol='RELIANCE'):
    """Create the candlestick chart with volume and moving averages."""

    required = {'date', 'open', 'high', 'low', 'close', 'volume'}

    if df is None or df.empty or not required.issubset(set(df.columns)):
        fig = go.Figure()
        fig.update_layout(
            **CHART_LAYOUT,
            annotations=[dict(
                text=f"Waiting for {symbol} market data…",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="#8888aa"),
            )],
        )
        return fig

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='#00d4aa',
            decreasing_line_color='#ff4757',
            increasing_fillcolor='#00d4aa',
            decreasing_fillcolor='#ff4757',
            name='Price',
            showlegend=False,
        ),
        row=1, col=1,
    )

    # SMA20
    if 'sma20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['sma20'],
                mode='lines',
                name='SMA 20',
                line=dict(color='#ff9900', width=1, dash='dot'),
            ),
            row=1, col=1,
        )

    # SMA50
    if 'sma50' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['sma50'],
                mode='lines',
                name='SMA 50',
                line=dict(color='#3b82f6', width=1, dash='dot'),
            ),
            row=1, col=1,
        )

    # Volume
    colors = ['#00d4aa' if c >= o else '#ff4757' for c, o in zip(df['close'], df['open'])]

    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            marker_color=colors,
            opacity=0.5,
            name='Volume',
            showlegend=False,
        ),
        row=2, col=1,
    )

    fig.update_layout(**CHART_LAYOUT)

    fig.update_layout(
        yaxis=dict(autorange=True, fixedrange=False),
        yaxis2=dict(
            gridcolor='#1e1e35',
            linecolor='#2a2a4a',
            tickfont=dict(size=9),
            side='right',
            autorange=True,
            fixedrange=False
        ),
    )

    return fig


def create_price_chart_panel(fig, symbols):
    """Create the full price chart panel with controls."""

    symbol_options = [{'label': f'{s}', 'value': s} for s in symbols]

    # ── OHLC BAR ─────────────────────────────
    ohlc_bar = html.Div(
        id="ohlc-bar",
        className="ohlc-bar",
        children=[
            html.Span("O: "),
            html.Span(id="ohlc-open"),

            html.Span("  H: "),
            html.Span(id="ohlc-high"),

            html.Span("  L: "),
            html.Span(id="ohlc-low"),

            html.Span("  C: "),
            html.Span(id="ohlc-close"),
        ]
    )

    return html.Div(
        className='panel',
        style={'gridRow': '1 / 2', 'gridColumn': '1 / 2'},
        children=[

            # ── Header ─────────────────────────
            html.Div(className='panel-header', children=[
                html.Span('PRICE CHART', className='panel-title'),

                html.Div(className='chart-controls', children=[
                    dcc.Dropdown(
                        id='chart-symbol-dropdown',
                        options=symbol_options,
                        value='RELIANCE',
                        clearable=False,
                        className='dash-dropdown',
                        style={'width': '110px'},
                    ),

                    html.Button('1D', id='tf-1d', className='timeframe-btn active', n_clicks=0),
                    html.Button('5D', id='tf-5d', className='timeframe-btn', n_clicks=0),
                    html.Button('1M', id='tf-1m', className='timeframe-btn', n_clicks=0),
                    html.Button('3M', id='tf-3m', className='timeframe-btn', n_clicks=0),
                    html.Button('1Y', id='tf-1y', className='timeframe-btn', n_clicks=0),
                ]),
            ]),

            # ── Body ───────────────────────────
            html.Div(className='panel-body', style={'padding': '0'}, children=[

                ohlc_bar,

                dcc.Graph(
                    id='price-chart',
                    figure=fig,
                    config={'displayModeBar': False, 'responsive': True},
                    style={'height': '100%'},
                ),

            ]),
        ]
    )