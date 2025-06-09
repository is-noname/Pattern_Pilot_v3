# app_dash.py - Pattern Pilot Professional Terminal
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import json
import os
import sys
import request

# Import your existing engine (unchanged!)
from core.market_engine import market_engine

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Pattern Pilot Pro"


def get_layout():
    """Professional Terminal Layout"""

    # Get available symbols from your existing engine
    available_symbols = market_engine.get_available_symbols()[:50]
    exchange_info = market_engine.get_exchange_info()

    # Header Bar
    exchange_indicators = []
    for name, info in exchange_info.items():
        status_class = "online" if info.get('status') == 'online' else "offline"
        exchange_indicators.append(
            html.Span([
                html.Span(className=f"exchange-dot {status_class}"),
                name.title()
            ], className="exchange-status")
        )

    current_time = datetime.now().strftime("%H:%M:%S UTC")

    header = html.Div([
        html.Div("Professional Trading Terminal", style={"fontWeight": "bold"}),
        html.Div(exchange_indicators),
        html.Div(current_time, id="time-display"),
    ], className="header-bar")


    # Main Trading Panel
    trading_panel = html.Div([
        # Controls Row
        html.Div([
            html.Div([
                html.Div("Symbol", className="control-label"),
                dcc.Dropdown(
                    id="symbol-dropdown",
                    options=[{"label": s, "value": s} for s in available_symbols],
                    value="BTC/USDT" if "BTC/USDT" in available_symbols else available_symbols[0],
                    clearable=False,
                    style={"width": "200px"}
                )
            ], className="control-group"),

            html.Div([
                html.Div("Timeframe", className="control-label"),
                dcc.Dropdown(
                    id="timeframe-dropdown",
                    options=[
                        {"label": "1m", "value": "1m"},
                        {"label": "5m", "value": "5m"},
                        {"label": "15m", "value": "15m"},
                        {"label": "1h", "value": "1h"},
                        {"label": "4h", "value": "4h"},
                        {"label": "1d", "value": "1d"},
                        {"label": "1w", "value": "1w"}
                    ],
                    value="1d",
                    clearable=False,
                    style={"width": "100px"}
                )
            ], className="control-group"),

            html.Div([
                html.Div("Candles", className="control-label"),
                dcc.Input(
                    id="limit-input",
                    type="number",
                    value=200,
                    min=50,
                    max=1000,
                    style={"width": "80px", "height": "36px", "background": "#2a2a2a",
                           "border": "1px solid #404040", "color": "#e0e0e0", "borderRadius": "4px"}
                )
            ], className="control-group"),

            html.Div([
                html.Div("Exchange", className="control-label"),
                dcc.Dropdown(
                    id="exchange-dropdown",
                    options=[{"label": "Auto", "value": "auto"}] +
                            [{"label": name.title(), "value": name} for name in market_engine.exchanges.keys()],
                    value="auto",
                    clearable=False,
                    style={"width": "120px"}
                )
            ], className="control-group"),

            html.Div([
                html.Div("", className="control-label"),  # Spacer
                html.Button("ANALYZE", id="analyze-btn", className="analyze-btn")
            ], className="control-group")
        ], className="controls-row"),

        html.Div([
            html.Button(
                "🛑 QUIT",
                id="shutdown-btn",
                style={
                    'position': 'fixed',
                    'top': '20px',
                    'right': '20px',
                    'background': '#ff4444',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'z-index': '9999'
                }
            )
        ]),

        # Verstecktes Div für Shutdown-Trigger
        html.Div(id="shutdown-trigger", style={"display": "none"}),

        # Chart Area
        html.Div([
            dcc.Graph(
                id="main-chart",
                figure=create_placeholder_chart(),
                style={"height": "600px"}
            )
        ], className="chart-container"),

        # Pattern Summary
        html.Div(id="pattern-summary")

    ], className="trading-panel")

    # News Sidebar
    news_sidebar = html.Div([
        html.H3("Market News & Analysis"),
        html.Div(id="news-feed", children=create_news_items())
    ], className="news-sidebar")

    # Status Bar
    status_bar = html.Div([
        html.Div([
            html.Div("$1.34T", className="status-value"), # noch statisch
            html.Div("Market Cap", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("2,847", className="status-value"), # noch statisch
            html.Div("24h Volume", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("73", className="status-value"), # noch statisch
            html.Div("Fear & Greed", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("BTC 52.3%", className="status-value"), # noch statisch
            html.Div("Dominance", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("1,247", className="status-value"), # noch statisch
            html.Div("Active Pairs", className="status-label")
        ], className="status-metric")
    ], className="status-bar")

    # Complete Layout
    return html.Div([
        header,
        html.Div([trading_panel, news_sidebar], className="main-container"),
        status_bar
    ])


def create_placeholder_chart():
    """Placeholder chart for initial load"""
    fig = go.Figure()
    fig.add_annotation(
        text="Select symbol and click ANALYZE to view chart",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#666")
    )
    fig.update_layout(
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(color="#e0e0e0"),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig


def create_news_items():
    """Generate news items (mock data)"""
    news_data = [
        {"type": "high", "text": "Bitcoin breaks $67k resistance, eyes $70k target", "time": "14:32"},
        {"type": "medium", "text": "Ethereum merge upgrade shows 15% staking yield increase", "time": "13:45"},
        {"type": "low", "text": "SOL network congestion resolved, TPS back to normal", "time": "12:18"},
        {"type": "high", "text": "Fed signals dovish stance in upcoming FOMC meeting", "time": "11:55"},
        {"type": "medium", "text": "Solana announces new trading pairs for institutional clients", "time": "10:30"},
        {"type": "high", "text": "Crypto adoption in emerging markets up 340% YoY", "time": "09:42"},
        {"type": "low", "text": "Major whale movements detected: 12,000 BTC moved", "time": "08:15"},
        {"type": "medium", "text": "DeFi TVL reaches new ATH at $84.5B across protocols", "time": "07:33"}
    ]

    news_items = []
    for item in news_data:
        badge_class = f"news-badge {item['type']}"
        news_items.append(
            html.Div([
                html.Span(item["type"].upper(), className=badge_class),
                html.Span(item["text"]),
                html.Div(item["time"], className="news-time")
            ], className="news-item")
        )

    return news_items


# Set layout
app.layout = get_layout()


# Callback for analysis
@app.callback(
    [Output("main-chart", "figure"),
     Output("pattern-summary", "children")],
    Input("analyze-btn", "n_clicks"),
    [Input("symbol-dropdown", "value"),
     Input("timeframe-dropdown", "value"),
     Input("limit-input", "value"),
     Input("exchange-dropdown", "value")]
)

# Shutdown Callback
@app.callback(
    Output("shutdown-trigger", "children"),
    Input("shutdown-btn", "n_clicks"),
    prevent_initial_call=True
)

def analyze_symbol(n_clicks, symbol, timeframe, limit, exchange):
    """Analyze symbol using your existing market engine"""

    if not n_clicks:
        return create_placeholder_chart(), html.Div()

    try:
        # Use your existing market engine (unchanged!)
        ex = None if exchange == 'auto' else exchange
        df = market_engine.get_ohlcv(symbol, timeframe, limit, ex)

        if df.empty:
            return create_error_chart(f"No data found for {symbol}"), html.Div(
                f"❌ No data found for {symbol}",
                style={"color": "#f44336", "padding": "16px"}
            )

        # Detect patterns using your existing engine
        patterns = market_engine.detect_patterns(df)

        # Create professional chart
        fig = create_professional_chart(df, patterns, symbol, timeframe)

        # Create pattern summary
        summary = create_pattern_summary(patterns, len(df))

        return fig, summary

    except Exception as e:
        return create_error_chart(f"Error: {str(e)}"), html.Div(
            f"❌ Error: {str(e)}",
            style={"color": "#f44336", "padding": "16px"}
        )


def shutdown_server(n_clicks):
    if n_clicks:
        # Server elegant beenden
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # Fallback für Production
            os._exit(0)
        func()
    return ""



def create_professional_chart(df, patterns, symbol, timeframe):
    """Create professional trading chart"""

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{symbol} {timeframe}', 'Volume')
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price",
            increasing_line_color='#4CAF50',
            decreasing_line_color='#f44336',
            increasing_fillcolor='#4CAF50',
            decreasing_fillcolor='#f44336'
        ),
        row=1, col=1
    )

    # Volume bars
    colors = ['#4CAF50' if close >= open else '#f44336'
              for close, open in zip(df['close'], df['open'])]

    fig.add_trace(
        go.Bar(
            x=df['datetime'],
            y=df['volume'],
            name="Volume",
            marker_color=colors,
            opacity=0.6
        ),
        row=2, col=1
    )

    # Add pattern markers
    pattern_colors = {
        'doji': '#ff9800',
        'hammer': '#4CAF50',
        'engulfing': '#f44336',
        'ma_crossover': '#2196F3',
        'support_resistance': '#9c27b0'
    }

    for pattern_name, signals in patterns.items():
        if not signals:
            continue

        color = pattern_colors.get(pattern_name, '#ffffff')

        for signal in signals:
            direction = signal.get('direction', 'neutral')
            if direction == 'bullish':
                color = '#4CAF50'
            elif direction == 'bearish':
                color = '#f44336'

            fig.add_trace(
                go.Scatter(
                    x=[signal['datetime']],
                    y=[signal['price']],
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        size=10,
                        color=color,
                        line=dict(width=2, color='white')
                    ),
                    name=pattern_name.replace('_', ' ').title(),
                    showlegend=False,
                    hovertemplate=f"<b>{pattern_name.replace('_', ' ').title()}</b><br>" +
                                  f"Price: ${signal['price']:.4f}<br>" +
                                  f"Direction: {direction}<br>" +
                                  f"Strength: {signal.get('strength', 0):.2f}<extra></extra>"
                ),
                row=1, col=1
            )

    # Professional styling
    fig.update_layout(
        height=600,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(family="Monaco, Consolas", size=10, color="#e0e0e0"),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # Grid styling
    fig.update_xaxes(gridcolor='#404040', gridwidth=1)
    fig.update_yaxes(gridcolor='#404040', gridwidth=1)

    return fig


def create_pattern_summary(patterns, candle_count):
    """Create pattern analysis summary"""

    if not patterns:
        return html.Div([
            html.H4("Pattern Analysis"),
            html.P(f"No significant patterns detected in {candle_count} candles.",
                   style={"color": "#666"})
        ], className="pattern-summary")

    # Calculate statistics
    all_signals = []
    for signals in patterns.values():
        all_signals.extend(signals)

    if not all_signals:
        return html.Div([
            html.H4("Pattern Analysis"),
            html.P("No patterns detected.", style={"color": "#666"})
        ], className="pattern-summary")

    bullish_count = len([s for s in all_signals if s.get('direction') == 'bullish'])
    bearish_count = len([s for s in all_signals if s.get('direction') == 'bearish'])
    avg_strength = sum(s.get('strength', 0) for s in all_signals) / len(all_signals)

    # Create summary content
    summary_content = [
        html.H4("Pattern Analysis"),
        html.Div([
            html.Span(f"🟢 {bullish_count} Bullish", style={"color": "#4CAF50", "marginRight": "16px"}),
            html.Span(f"🔴 {bearish_count} Bearish", style={"color": "#f44336", "marginRight": "16px"}),
            html.Span(f"💪 {avg_strength:.2f} Avg Strength", style={"color": "#ff9800"})
        ], style={"marginBottom": "12px"}),

        html.Div([
            html.P(
                f"Detected {len(all_signals)} signals across {len(patterns)} pattern types in {candle_count} candles.",
                style={"fontSize": "11px", "color": "#999", "margin": "0"})
        ])
    ]

    return html.Div(summary_content, className="pattern-summary")


def create_error_chart(error_message):
    """Create error chart"""
    fig = go.Figure()
    fig.add_annotation(
        text=error_message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#f44336")
    )
    fig.update_layout(
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(color="#e0e0e0"),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8050)