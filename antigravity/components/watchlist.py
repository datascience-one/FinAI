"""
Watchlist Component — Securities data table with Bloomberg styling.
"""

from dash import html, dash_table
import pandas as pd


def create_watchlist_panel(df):
    """Create the watchlist panel with a styled DataTable."""

    columns = [
        {'name': 'Symbol', 'id': 'Symbol'},
        {'name': 'Last', 'id': 'Last', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
        {'name': 'Chg', 'id': 'Change', 'type': 'numeric', 'format': {'specifier': '+,.2f'}},
        {'name': '%Chg', 'id': '%Chg', 'type': 'numeric', 'format': {'specifier': '+,.2f'}},
        {'name': 'Volume', 'id': 'Volume'},
        {'name': 'Bid', 'id': 'Bid', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
        {'name': 'Ask', 'id': 'Ask', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
        {'name': 'High', 'id': 'High', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
        {'name': 'Low', 'id': 'Low', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
    ]

    table = dash_table.DataTable(
        id='watchlist-table',
        columns=columns,
        data=df.to_dict('records'),
        sort_action='native',
        sort_mode='single',
        page_action='none',
        style_table={
            'overflowY': 'auto',
            'overflowX': 'auto',
            'height': '100%',
        },
        style_header={
            'backgroundColor': '#0f0f23',
            'color': '#ff9900',
            'fontFamily': 'JetBrains Mono, Consolas, monospace',
            'fontSize': '10px',
            'fontWeight': '600',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'border': 'none',
            'borderBottom': '1px solid #ff990055',
            'padding': '8px 10px',
        },
        style_cell={
            'backgroundColor': '#141428',
            'color': '#e8e8f0',
            'fontFamily': 'JetBrains Mono, Consolas, monospace',
            'fontSize': '11px',
            'border': 'none',
            'borderBottom': '1px solid #1a1a35',
            'padding': '6px 10px',
            'textAlign': 'right',
            'minWidth': '70px',
        },
        style_cell_conditional=[
            {'if': {'column_id': 'Symbol'}, 'textAlign': 'left', 'fontWeight': '600', 'color': '#ff9900'},
        ],
        style_data_conditional=[
            # Green for positive changes
            {
                'if': {
                    'filter_query': '{Change} > 0',
                    'column_id': 'Change',
                },
                'color': '#00d4aa',
            },
            {
                'if': {
                    'filter_query': '{%Chg} > 0',
                    'column_id': '%Chg',
                },
                'color': '#00d4aa',
            },
            # Red for negative changes
            {
                'if': {
                    'filter_query': '{Change} < 0',
                    'column_id': 'Change',
                },
                'color': '#ff4757',
            },
            {
                'if': {
                    'filter_query': '{%Chg} < 0',
                    'column_id': '%Chg',
                },
                'color': '#ff4757',
            },
            # Row hover effect
            {
                'if': {'state': 'active'},
                'backgroundColor': '#1a1a35',
                'border': 'none',
            },
        ],
        style_as_list_view=True,
    )

    return html.Div(className='panel', style={'gridRow': '2 / 3', 'gridColumn': '1 / 2'}, children=[
        html.Div(className='panel-header', children=[
            html.Span('WATCHLIST', className='panel-title'),
            html.Span('20 Securities', className='panel-subtitle'),
        ]),
        html.Div(className='panel-body', style={'padding': '0'}, children=[table]),
    ])
