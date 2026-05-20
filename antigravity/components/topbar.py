"""
Top Bar Component — Bloomberg-style command bar with branding and clock.
"""

from dash import html, dcc


def create_topbar():
    """Create the Bloomberg-style top command bar."""
    return html.Div(
        className='topbar',
        children=[
            # Brand
            html.Span('BLOOMBERG', className='topbar-brand'),
            html.Div(className='topbar-separator'),

            # Command input
            dcc.Input(
                id='command-input',
                type='text',
                placeholder='Enter command or search securities... (e.g., AAPL <EQUITY> GP)',
                className='command-input',
                debounce=True,
            ),

            html.Div(className='topbar-separator'),

            # Clock
            html.Div(id='topbar-clock', className='topbar-clock', children='--:--:--'),

            html.Div(className='topbar-separator'),

            # Connection status
            html.Div(className='topbar-status', children=[
                html.Div(className='status-dot'),
                html.Span('LIVE', className='status-text'),
            ]),
        ]
    )
