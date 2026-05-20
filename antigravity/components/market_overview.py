"""
Market Overview Component — Scrolling ticker tape and index summary cards.
"""

from dash import html


def create_ticker_tape(ticker_data):
    """Create the scrolling ticker tape marquee."""
    items = []
    for t in ticker_data:
        change_class = 'ticker-change-up' if t['change'] >= 0 else 'ticker-change-down'
        arrow = '▲' if t['change'] >= 0 else '▼'
        sign = '+' if t['change'] >= 0 else ''

        items.append(
            html.Div(className='ticker-item', children=[
                html.Span(t['symbol'], className='ticker-symbol'),
                html.Span(f"₹{t['price']:,.2f}", className='ticker-price'),
                html.Span(
                    f"{arrow} {sign}{t['change_pct']:.2f}%",
                    className=change_class,
                ),
                html.Span('│', className='ticker-divider'),
            ])
        )

    # Duplicate for seamless scroll loop
    return html.Div(
        className='ticker-tape-wrapper',
        children=[
            html.Div(
                id='ticker-tape',
                className='ticker-tape',
                children=items + items,  # doubled for infinite scroll
            )
        ]
    )


def create_index_cards(index_data):
    """Create market index summary cards."""
    cards = []
    for idx in index_data:
        change_class = 'change-positive' if idx['change'] >= 0 else 'change-negative'
        sign = '+' if idx['change'] >= 0 else ''
        arrow = '▲' if idx['change'] >= 0 else '▼'

        # Format value based on magnitude
        if idx['value'] > 1000:
            value_str = f"{idx['value']:,.2f}"
        else:
            value_str = f"{idx['value']:.2f}"

        cards.append(
            html.Div(className='index-card', children=[
                html.Div(idx['name'], className='index-card-name'),
                html.Div(value_str, className='index-card-value'),
                html.Div(
                    f"{arrow} {sign}{idx['change']:.2f} ({sign}{idx['change_pct']:.2f}%)",
                    className=f'index-card-change {change_class}',
                ),
            ])
        )

    return html.Div(id='index-cards', className='index-cards-row', children=cards)


def create_market_overview(ticker_data, index_data):
    """Create the full market overview section."""
    return html.Div([
        create_ticker_tape(ticker_data),
        create_index_cards(index_data),
    ])
