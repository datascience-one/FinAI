"""
News Feed Component — Live scrolling news panel with headlines and source tags.
"""

from dash import html


def create_news_item(news):

    timestamp = news.get("timestamp", "")
    headline = news.get("headline", "")
    source = news.get("source", "")
    category = news.get("category", "")
    link = news.get("link")

    # If a link exists, make headline clickable
    if link:
        headline_component = html.A(
            headline,
            href=link,
            target="_blank",
            rel="noopener noreferrer",
            className="news-headline",
            style={
                "textDecoration": "none",
                "color": "#4cc9f0",
                "cursor": "pointer"
            }
        )
    else:
        headline_component = html.Span(
            headline,
            className="news-headline",
            style={"color": "#e8e8f0"}
        )

    return html.Div(
        className="news-item",
        children=[

            html.Div(
                className="news-timestamp",
                children=[html.Span(timestamp)]
            ),

            headline_component,

            html.Div(
                children=[
                    html.Span(source, className="news-source-tag"),
                    html.Span(category, className="news-category-tag")
                ]
            ),
        ]
    )


def create_news_panel(news_data):

    news_items = [create_news_item(n) for n in news_data]

    return html.Div(
        className="panel",
        style={'gridRow': '1 / 2', 'gridColumn': '2 / 3'},
        children=[

            html.Div(
                className="panel-header",
                children=[
                    html.Span("NEWS FEED", className="panel-title"),
                    html.Span("REAL-TIME", className="panel-subtitle"),
                ],
            ),

            html.Div(
                id="news-feed-body",
                className="panel-body",
                style={'padding': '0'},
                children=news_items,
            ),
        ],
    )