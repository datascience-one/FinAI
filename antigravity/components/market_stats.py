"""
Market Stats Component — Key market metrics and indicator cards.
"""

from dash import html
import plotly.graph_objects as go
from dash import dcc


def create_stat_card(label, value, change=None, change_positive=None, unit=''):
    """Create a single stat card."""
    children = [
        html.Div(label, className='stat-label'),
        html.Div(f"{value}{unit}", className='stat-value'),
    ]

    if change is not None:
        change_class = 'stat-change '
        if change_positive is True:
            change_class += 'change-positive'
        elif change_positive is False:
            change_class += 'change-negative'
        else:
            change_class += 'text-secondary'
        children.append(html.Div(change, className=change_class))

    return html.Div(className='stat-card', children=children)


def _safe_fmt(val, fmt='{0}', prefix='', suffix=''):
    """Format a value safely — return 'N/A' if value is 'N/A' or None."""
    if val == 'N/A' or val is None:
        return 'N/A'
    try:
        return f"{prefix}{fmt.format(val)}{suffix}"
    except (ValueError, TypeError):
        return 'N/A'


def create_market_stats_panel(stats):
    """Create the market stats panel with India market data."""
    vix_val = stats.get('india_vix', 'N/A')

    mkt_status = stats.get('market_status', 'Unknown')
    mkt_open = str(mkt_status).upper() in ('OPEN', 'NORMAL MARKET')

    # VIX change label (only compare if numeric)
    if isinstance(vix_val, (int, float)):
        vix_change = 'Low Vol' if vix_val < 15 else 'Elevated'
        vix_positive = vix_val < 15
    else:
        vix_change = None
        vix_positive = None

    # Put/Call label
    pc_val = stats.get('put_call', 'N/A')
    if isinstance(pc_val, (int, float)):
        pc_change = 'Bullish' if pc_val < 0.9 else 'Bearish'
        pc_positive = pc_val < 0.9
    else:
        pc_change = None
        pc_positive = None

    cards = [
        create_stat_card('India VIX', vix_val,
                         change=vix_change,
                         change_positive=vix_positive),

        create_stat_card('Bank NIFTY', _safe_fmt(stats.get('bank_nifty', 'N/A'), '{0:,.2f}')),

        create_stat_card('Adv/Decl', stats.get('adv_decl', 'N/A')),

        create_stat_card('USD/INR', _safe_fmt(stats.get('usd_inr', 'N/A'), '{0:.2f}', prefix='₹')),

        create_stat_card('Gold MCX', _safe_fmt(stats.get('gold_mcx', 'N/A'), '{0:,.0f}', prefix='₹')),

        create_stat_card('Crude MCX', _safe_fmt(stats.get('crude_mcx', 'N/A'), '{0:,.0f}', prefix='₹')),

        create_stat_card('Put/Call', pc_val,
                         change=pc_change,
                         change_positive=pc_positive),

        create_stat_card('FII/DII', stats.get('fii_dii', 'N/A')),

        create_stat_card('Turnover', stats.get('mkt_turnover', 'N/A')),

        create_stat_card('New Highs', stats.get('new_highs', 'N/A'),
                         change=f"Lows: {stats.get('new_lows', 'N/A')}"),

        create_stat_card('Market', mkt_status,
                         change='NSE · BSE',
                         change_positive=mkt_open),

        create_stat_card('52W Highs', stats.get('new_highs', 'N/A')),
    ]

    return html.Div(className='panel', style={'gridRow': '2 / 3', 'gridColumn': '2 / 3'}, children=[
        html.Div(className='panel-header', children=[
            html.Span('MARKET STATS', className='panel-title'),
            html.Span('KEY INDICATORS', className='panel-subtitle'),
        ]),
        html.Div(
            id='market-stats-body',
            className='panel-body',
            children=[
                html.Div(className='stats-grid', children=cards),
            ]
        ),
    ])
