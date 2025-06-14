# app.py - Pattern Pilot Terminal
"""
Pattern Pilot 3.0 Terminal - Hauptanwendung (Dash)

Implementiert ein professionelles Trading-Terminal mit interaktiven Charts,
Pattern-Detection und Multi-Exchange-Support. Nutzt Dash für die UI und
verbindet sich mit der market_engine für Daten und Pattern-Analyse.

Enthält alle UI-Callbacks, Chart-Rendering und Layout-Definitionen.

Features:
- Interaktive Candlestick-Charts mit Pattern-Overlay
- Echtzeit Exchange-Status mit Background-Threading
- Dynamisches Pattern-Filtering
- Responsive Layout für Desktop-Anwendungen

Technologie-Stack:
- Dash (Flask + React)
- Plotly für interaktive Charts
- market_engine für Exchange-Connection und Pattern-Detection
"""
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import json
import os
import sys
from flask import request

# Import your existing engine and settings
from core.market_engine import market_engine
from core.analysis_pipeline import analysis_pipeline
from config.settings import UI_CONFIG, PATTERN_CONFIG, CHART_CONFIG
from config.pattern_settings import TIMEFRAME_CONFIGS

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Holy Dashboard 3.1"



#==============================================================================
# region               📊 CHART GENERATION HELPERS
#==============================================================================
def create_loading_chart():
    """
    Erstellt einen Loading-Chart während Exchanges initialisiert werden.

    Zeigt eine benutzerfreundliche Warteanzeige mit "Exchanges werden geladen"
    Nachricht auf dunklem Hintergrund.

    Returns:
        go.Figure: Plotly Figure mit Loading-Anzeige
    """
    fig = go.Figure()
    fig.add_annotation(
        text="⏳ Exchanges werden geladen... Bitte warten",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#ffaa00")
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
# endregion

#==============================================================================
# region               🎨 DASHBOARD LAYOUT & COMPONENTS
#==============================================================================
def get_layout():
    """Terminal Layout"""
    """
    Generiert das komplette Dashboard-Layout der Anwendung.

    Erstellt eine strukturierte UI mit:
    - Header-Bar mit Exchange-Status und Echtzeit-Uhr
    - Trading-Panel mit Controls, Chart und Pattern-Summary
    - News-Sidebar für Market-News
    - Status-Bar mit Marktmetriken

    Initialisiert auch die Background-Thread-Kommunikation und Daten-Stores.

    Returns:
        html.Div: Das vollständige Dashboard-Layout als Dash HTML-Struktur
    """

    # Get available symbols from your existing engine
    available_symbols = market_engine.get_available_symbols()[:50]
    exchange_info = market_engine.get_exchange_info()
    # Check ob Exchanges laden
    exchanges_loading = all(isinstance(ex, dict) and ex.get('status') == 'loading'
                            for ex_name, ex in market_engine.exchanges.items())

    # •••••••••••••••••••••••••• 🔝 Header Bar Components •••••••••••••••••••••••••• #
    exchange_indicators = []
    for name, info in exchange_info.items():
        # Status-Klasse und Icon basierend auf Exchange-Status
        if info.get('status') == 'loading':
            status_class = "loading"
            status_icon = "⏳"
        elif info.get('status') == 'online':
            status_class = "online"
            status_icon = "✅"
        else:
            status_class = "offline"
            status_icon = "❌"

        # Individuelles ID für jeden Exchange-Status-Indikator für Callback-Updates
        exchange_indicators.append(
            html.Span([
                html.Span(className=f"exchange-dot {status_class}"),
                f"{name.title()}"
            ], className="exchange-status", id=f"exchange-status-{name}")
        )

    current_time = datetime.now().strftime("%H:%M:%S UTC")

    header = html.Div([
        html.Div("Holy Terminal v3.0", style={"fontWeight": "bold"}),
        html.Div(exchange_indicators),
        html.Div(current_time, id="time-display"),
    ], className="header-bar")

    interval = dcc.Interval(
        id='clock-interval',
        interval=UI_CONFIG['clock_interval'],  # 2 Sekunde in Millisekunden
        n_intervals=0
    )

    # Speicherort für Exchange-Status - ermöglicht Aktualisierungen ohne Page-Reload
    exchange_status_store = dcc.Store(id='exchange-status-store', data={})

    # Interval für Background-Thread-Kommunikation
    exchange_interval = dcc.Interval(
        id='exchange-update-interval',
        interval=UI_CONFIG['exchange_interval'],  # Polling-Frequenz: 1000ms
        n_intervals=0
    )

    # •••••••••••••••••••••••••• 📉 Main Panel Components •••••••••••••••••••••••••• #

    chart_patterns = set()
    for timeframe_config in TIMEFRAME_CONFIGS.values():
        chart_patterns.update(timeframe_config.keys())

    # Kombinierte Pattern-Optionen #
    pattern_options = [{"label": "All Patterns", "value": "all"}]

    # Candlestick Patterns mit Icon
    pattern_options += [
        {"label": f"📊 {name.replace('_', ' ').title()}", "value": name}
        for name in PATTERN_CONFIG['candlestick_patterns']
    ]

    # Chart Patterns mit Icon
    pattern_options += [
        {"label": f"📈 {name.replace('_', ' ').title()}", "value": name}
        for name in sorted(chart_patterns)
    ]


    trading_panel = html.Div([
        # •••••••••••••••••••••••••• Controls Row •••••••••••••••••••••••••• #
        html.Div([
            html.Div([
                html.Div("Symbol", className="control-label"),
                dcc.Dropdown(
                    id="symbol-dropdown",
                    options=[{"label": s, "value": s} for s in available_symbols],
                    value="BTC/USDT" if "BTC/USDT" in available_symbols else (available_symbols[0] if available_symbols else ""),
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
                        {"label": "3d", "value": "3d"},
                        {"label": "1w", "value": "1w"},
                        {"label": "1M", "value": "1M"}
                    ],
                    value=CHART_CONFIG['default_timeframe'],  # Default aus settings.py
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
                "[X]",
                id="shutdown-btn",
                style={
                    'position': 'fixed',
                    'top': '50px',              # 👈 HIER ÄNDERN - Abstand von oben
                    'right': '16px',            # 👈 HIER ÄNDERN - Abstand von rechts
                    'background': '#ff4444',    # 👈 HIER ÄNDERN - Hintergrundfarbe
                    'color': 'white',           # 👈 HIER ÄNDERN - Textfarbe
                    'border': 'none',
                    'padding': '10px 20px',     # 👈 HIER ÄNDERN - Innenabstand
                    'border-radius': '5px',     # 👈 HIER ÄNDERN - Abrundung
                    'cursor': 'pointer',
                    'z-index': '9999'
                }
            )
        ]),

        # Verstecktes Div für Shutdown-Trigger
        html.Div(id="shutdown-trigger", style={"display": "none"}),

        # •••••••••••••••••••••••••• Filter Panel •••••••••••••••••••••••••• #
        html.Div([
            html.Div([
                html.Div("Pattern Filter", className="control-label"),

                dcc.Dropdown(
                    id="pattern-type-filter",
                    options=pattern_options,  # <-- Nutze kombinierte Liste
                    value="all",
                    clearable=False,
                    multi=True,
                    style={"width": "100%"}
                )
            ], className="control-group", style={"flex": "2"}),

            html.Div([
                html.Div("Direction", className="control-label"),
                dcc.Checklist(
                    id="direction-filter",
                    options=[
                        {"label": "Bullish", "value": "bullish"},
                        {"label": "Bearish", "value": "bearish"},
                        {"label": "Support", "value": "support"},
                        {"label": "Resistance", "value": "resistance"},
                        {"label": "Neutral", "value": "neutral"}
                    ],
                    value=["bullish", "bearish", "support", "resistance", "neutral"],
                    inline=True,
                    labelStyle={"marginRight": "12px", "color": "#e0e0e0"}
                )
            ], className="control-group", style={"flex": "3"}),

            html.Div([
                html.Div("Min Strength", className="control-label"),
                dcc.Slider(
                    id="strength-filter",
                    min=0,
                    max=1,
                    step=0.1,
                    value=0.5,
                    marks={i / 10: {"label": str(i / 10), "style": {"color": "#e0e0e0"}} for i in range(0, 11)},
                )
            ], className="control-group", style={"flex": "2"})
        ], className="filter-row"),

        # Pattern Count Badge - direkt nach dem Filter-Panel
        html.Div([
            html.Span(id="pattern-count-badge", className="pattern-count"),
            html.Span("Patterns Found", className="pattern-label")
        ], className="pattern-count-container"),

        # •••••••••••••••••••••••••• Chart Area •••••••••••••••••••••••••• #
        html.Div([
            dcc.Graph(
                id="main-chart",
                figure=create_loading_chart() if exchanges_loading else create_placeholder_chart(),
                style={"height": "600px"}
            )
        ], className="chart-container"),

        # •••••••••••••••••••••••••• Pattern Summary •••••••••••••••••••••••••• #
        html.Div(id="pattern-summary")

    ], className="trading-panel")

    # •••••••••••••••••••••••••• 📉 News Sidebar Components •••••••••••••••••••••••••• #
    news_sidebar = html.Div([
        html.H3("Market News & Analysis"),
        html.Div(id="news-feed", children=create_news_items())
    ], className="news-sidebar")

    # •••••••••••••••••••••••••• 📉 Status Bar Components •••••••••••••••••••••••••• #
    status_bar = html.Div([
        html.Div([
            html.Div("--", id="market-cap-value", className="status-value"), # noch statisch?
            html.Div("Market Cap", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("--", id="volume-value", className="status-value"), # noch statisch?
            html.Div("24h Volume", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("--", id="fear-greed-value", className="status-value"), # noch statisch?
            html.Div("Fear & Greed", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("--", id="dominance-value", className="status-value"), # noch statisch?
            html.Div("Dominance", className="status-label")
        ], className="status-metric"),

        html.Div([
            html.Div("--", id="pairs-value", className="status-value"), # noch statisch?
            html.Div("Active Pairs", className="status-label")
        ], className="status-metric")
    ], className="status-bar")

    # •••••••••••••••••••••••••• 📉 Complete Layout •••••••••••••••••••••••••• #
    return html.Div([
        header,
        interval,
        exchange_interval,  # Background-Thread Monitoring
        exchange_status_store,  # Zentraler Status-Speicher
        html.Div([trading_panel, news_sidebar], className="main-container"),
        status_bar
    ])

# endregion

#==============================================================================
# region               📈 CHART RENDERING & VISUALIZATION
#==============================================================================
def create_placeholder_chart():
    """
    Placeholder chart for initial load

    Erstellt einen leeren Platzhalter-Chart für den initialen App-Zustand.

    Zeigt eine Anleitung "Select symbol and click ANALYZE to view chart"
    auf dunklem Hintergrund.

    Returns:
        go.Figure: Plotly Figure mit Platzhalter-Anzeige
    """

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
    """
    Generate news items (mock data)
    Generiert News-Items für die Sidebar (derzeit Mock-Daten).

    Erstellt eine Liste von formatierten News-Elementen mit verschiedenen
    Prioritäten (high, medium, low) und Zeitstempeln.

    Returns:
        list: Liste von html.Div Elementen mit News-Einträgen
    """
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
# endregion

#==============================================================================
# region               🔄 CALLBACKS & INTERAKTIONEN (Callback for analysis)
#==============================================================================
@app.callback(
    [Output("main-chart", "figure"),
     Output("pattern-summary", "children"),
     Output("pattern-count-badge", "children")],  # Filter-Input
    Input("analyze-btn", "n_clicks"),
    [Input("symbol-dropdown", "value"),
     Input("timeframe-dropdown", "value"),
     Input("limit-input", "value"),
     Input("exchange-dropdown", "value")],
    [Input("pattern-type-filter", "value"),  # Filter-Input
     Input("direction-filter", "value"),  # Filter-Input
     Input("strength-filter", "value")]  # Filter-Input
)
def analyze_symbol(n_clicks, symbol, timeframe, limit, exchange, pattern_types, directions, min_strength):
    """
       Hauptanalyse-Callback für Trading-Symbole.

       Wird ausgelöst durch den ANALYZE-Button. Holt OHLCV-Daten vom Market Engine,
       detektiert Patterns und generiert Chart-Visualisierung mit gefilterten
       Pattern-Overlays basierend auf Benutzereinstellungen.

       Args:
           n_clicks (int): Button-Klick-Counter (Trigger)
           symbol (str): Trading-Pair (z.B. "BTC/USDT")
           timeframe (str): Zeitrahmen (z.B. "1d", "4h")
           limit (int): Anzahl der Candles (50-1000)
           exchange (str): Exchange-Name oder "auto" für Auto-Routing
           pattern_types (list/str): Liste der zu zeigenden Pattern-Typen oder "all"
           directions (list): Zu filternde Richtungen (bullish, bearish, etc.)
           min_strength (float): Minimale Signalstärke (0.0-1.0)

       Returns:
           tuple: (Chart-Figure, Pattern-Summary, Pattern-Count)
       """

    if not n_clicks:
        return create_placeholder_chart(), html.Div(), 0  # Nullwert für Counter
    # Keine Exchanges verfügbar? Early return
    if not symbol or all(isinstance(ex, dict) for ex in market_engine.exchanges.values()):
        return create_loading_chart(), html.Div("Exchanges werden geladen...",
                                                style={"color": "#ffaa00", "padding": "16px"}), 0  # Nullwert für Counter

    try:
        # Use your existing market engine (unchanged!)
        ex = None if exchange == 'auto' else exchange
        df = market_engine.get_ohlcv(symbol, timeframe, limit, ex)

        if df.empty:
            return create_error_chart(f"No data found for {symbol}"), html.Div(
                f"❌ No data found for {symbol}",
                style={"color": "#f44336", "padding": "16px"}
            ), 0  # Nullwert für Counter

        # Detect patterns using your existing engine
        patterns = market_engine.detect_patterns(df)

        # •••••••••••••••••••••••••• Filter patterns •••••••••••••••••••••••••• #
        if pattern_types != "all":
            pattern_filter = pattern_types  # Liste von gewählten Pattern-Typen
        else:
            pattern_filter = None  # Alle Pattern-Typen

        filtered_patterns = market_engine.filter_patterns(
            patterns,
            min_strength=min_strength,
            directions=directions,
            pattern_types=pattern_filter
        )

        # Create chart
        fig = create_professional_chart(df, filtered_patterns, symbol, timeframe)

        # Create pattern summary
        summary = create_pattern_summary(filtered_patterns, len(df))

        # Total Patterns = all filtered patterns
        #total_patterns = sum(len(signals) for signals in filtered_patterns.values())
        total_patterns = analysis_pipeline.get_pattern_count(symbol, timeframe)

        return fig, summary, total_patterns

    except Exception as e:
        return create_error_chart(f"Error: {str(e)}"), html.Div(
            f"❌ Error: {str(e)}",
            style={"color": "#f44336", "padding": "16px"}
        ), 0  # Nullwert für Counter


# Shutdown Callback
@app.callback(
    Output("shutdown-trigger", "children"),
    Input("shutdown-btn", "n_clicks"),
    prevent_initial_call=True
)
def shutdown_server(n_clicks):
    """
    Beendet den Dash-Server sauber bei [X]-Button-Klick.

    Versucht zuerst die werkzeug.server.shutdown Funktion aufzurufen,
    oder verwendet os._exit() als Fallback für Produktionsumgebungen.

    Args:
        n_clicks (int): Button-Klick-Counter

    Returns:
        str: Leerer String für Dash Output
    """
    if n_clicks:
        # Server elegant beenden
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # Fallback für Production
            os._exit(0)
        func()
    return ""
# endregion

# ==============================================================================
# region                     Create Trading Chart
# ==============================================================================
def create_professional_chart(df, patterns, symbol, timeframe):
    """Create trading chart"""
    """
    Erstellt einen professionellen Trading-Chart mit Pattern-Overlay.

    Generiert einen zweiteiligen Chart mit Candlestick-Daten oben (70%) und
    Volume-Daten unten (30%). Fügt Pattern-Marker basierend auf erkannten Signalen
    und deren Stärke hinzu. Verwendet ein dunkles Trading-Terminal-Theme.

    Args:
        df (pd.DataFrame): OHLCV-Daten im pandas DataFrame
        patterns (dict): Dictionary mit erkannten Pattern-Signalen
        symbol (str): Trading-Symbol für Chart-Titel
        timeframe (str): Zeitrahmen für Chart-Titel

    Returns:
        plotly.graph_objects.Figure: Vollständiger Trading-Chart
    """

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{symbol} {timeframe}', 'Volume')
    )

    # •••••••••••••••••••••••••• Candlestick chart •••••••••••••••••••••••••• #
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="",
            increasing_line_color='#06fc99',
            decreasing_line_color='#f44336',
            increasing_fillcolor='#06fc99',
            decreasing_fillcolor='#f44336',
        ),
        row=1, col=1
    )

    # •••••••••••••••••••••••••• Volume bars •••••••••••••••••••••••••• #
    colors = ['#06fc99' if close >= open else '#f44336'
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
    # 🎯 Enhanced Pattern Overlays with unique icons
    pattern_styles = PATTERN_CONFIG['pattern_styles']

    pattern_legend_added = set()  # Track which patterns are in legend

    for pattern_name, signals in patterns.items():
        if not signals:
            continue

        style = pattern_styles.get(pattern_name, {
            'symbol': 'circle',
            'color': '#ffffff',
            'size': 12,
            'emoji': '📊'
        })

        for i, signal in enumerate(signals):
            direction = signal.get('direction', 'neutral')
            strength = signal.get('strength', 0.5)

            # Color adjustment based on directions (from settings.py)
            # if 'direction' in style and direction in style['direction']:
            #     # Neue Struktur mit richtungsabhängigen Farben verwenden
            #     color = style['direction'][direction]['color']
            # else:
                # Fallback auf die Standard-Farbe
           #     color = style['color']

            if direction == 'bullish':
                color = style['color']
            elif direction == 'bearish':
                color = style['color']
            elif direction == 'resistance':
                color = style['color']
            elif direction == 'support':
                color = style['color']
            else:
                color = style['color']

            # Show legend only for first occurrence of each pattern
            show_legend = pattern_name not in pattern_legend_added
            if show_legend:
                pattern_legend_added.add(pattern_name)

            # Enhanced pattern marker
            fig.add_trace(
                go.Scatter(
                    x=[signal['datetime']],
                    y=[signal['price']* 1.1],  # 👈 Pattern Symbol über Kerze (1.005 Standard)
                    mode='markers',
                    marker=dict(
                        symbol=style['symbol'],
                        size=style['size'] + (strength * 8),  # Size based on strength
                        color=color,
                        line=dict(width=1, color='white'),
                        opacity=0.8 + (strength * 0.2)
                    ),
                    name=f"{style['emoji']} {pattern_name.replace('_', ' ').title()}",
                    hovertemplate=f"<b>{style['emoji']} {pattern_name.replace('_', ' ').title()}</b><br>" +
                                  f"Direction: {direction}<br>" +
                                  f"Strength: {strength:.2f}<br>" +
                                  f"Price: ${signal['price']:.4f}<br>" +
                                  f"Time: %{{x}}<extra></extra>",
                    showlegend=show_legend,
                    legendgroup=pattern_name
                ),
                row=1, col=1
            )

    # ================================================================================
    # 🎨 PATTERN OVERLAYS mit lokalen Plotly Dispatchers
    # ================================================================================

    print(f"🎨 Adding pattern overlays... Found {len(patterns)} pattern types")

    pattern_count = 0

    for pattern_name, pattern_list in patterns.items():
        if not pattern_list:  # Skip leere Listen
            continue

        print(f"   Processing {pattern_name}: {len(pattern_list)} patterns")

        for pattern in pattern_list:
            # Stelle sicher, dass Pattern den type hat
            if 'type' not in pattern:
                pattern['type'] = pattern_name

            try:
                # ✅ DOUBLE BOTTOM/TOP Integration
                if pattern_name in ['double_bottom', 'double_top']:
                    from core.patterns.chart_patterns.double_patterns import render_pattern_plotly

                    # Rendere Pattern mit lokalem Dispatcher
                    render_pattern_plotly(fig, df, pattern)
                    pattern_count += 1

                    print(
                        f"      ✅ Rendered {pattern_name} - P1: {pattern.get('P1')}, P2: {pattern.get('P2')}, Confirmed: {pattern.get('confirmed', False)}")

                # ✅ FALLBACK für andere Pattern-Typen (alte Marker-Methode)
                else:
                    # Verwende bestehende Pattern-Marker-Logik für andere Patterns
                    _add_legacy_pattern_marker(fig, df, pattern, pattern_name)
                    pattern_count += 1
                    print(f"      ➤ Legacy marker for {pattern_name}")

            except ImportError as e:
                print(f"      ⚠️ Plotly Renderer nicht verfügbar für {pattern_name}: {e}")
                # Fallback auf alte Marker-Methode
                _add_legacy_pattern_marker(fig, df, pattern, pattern_name)

            except Exception as e:
                print(f"      ❌ Fehler beim Rendern von {pattern_name}: {e}")
                import traceback
                traceback.print_exc()

    print(f"🎨 {pattern_count} Patterns als Overlays gerendert")



    # Professional styling
    fig.update_layout(
        height=CHART_CONFIG['height'],
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(family="Monaco, Consolas", size=10, color="#e0e0e0"),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"  # Zeigt Hover-Info für alle Traces an einem X-Punkt
    )

    # X-Achse mit Fadenkreuz
    fig.update_xaxes(
        gridcolor='#404040',
        gridwidth=1,
        showspikes=True,  # Zeigt vertikale Spike-Linie
        spikethickness=1,  # Dicke der Linie
        spikecolor="#06fc99",  # Farbe der Linie (Canto Green)
        spikemode="across",  # Geht über den ganzen Chart
        spikesnap="cursor"  # Folgt genau dem Cursor
    )

    # Y-Achse mit Fadenkreuz
    fig.update_yaxes(
        gridcolor='#404040',
        gridwidth=1,
        showspikes=True,  # Zeigt horizontale Spike-Linie
        spikethickness=1,  # Dicke der Linie
        spikecolor="#06fc99",  # Farbe der Linie (Canto Green)
        spikemode="across",  # Geht über den ganzen Chart
        spikesnap="cursor"  # Folgt genau dem Cursor
    )

    # Grid styling
    fig.update_xaxes(gridcolor='#404040', gridwidth=1)
    fig.update_yaxes(gridcolor='#404040', gridwidth=1)

    return fig


def _add_legacy_pattern_marker(fig, df, pattern, pattern_name):
    """
    Fallback: Einfache Marker für Patterns ohne spezifischen Plotly Renderer
    """
    try:
        # Finde einen representative Punkt im Pattern
        if 'P1' in pattern:
            x_pos = df.index[pattern['P1']]
            y_pos = df['close'].iloc[pattern['P1']]
        elif 'start_idx' in pattern:
            x_pos = df.index[pattern['start_idx']]
            y_pos = df['close'].iloc[pattern['start_idx']]
        else:
            return  # Kein sinnvoller Punkt gefunden

        # Bestimme Farbe basierend auf Pattern-Richtung
        color = 'lime' if 'bullish' in pattern_name or 'bottom' in pattern_name else 'red'

        # Einfacher Marker
        fig.add_trace(go.Scatter(
            x=[x_pos],
            y=[y_pos],
            mode='markers',
            marker=dict(
                color=color,
                size=10,
                symbol='star'
            ),
            name=pattern_name.replace('_', ' ').title(),
            showlegend=False,
            hovertemplate=f"<b>{pattern_name}</b><br>" +
                          "Price: $%{y:.4f}<extra></extra>"
        ))

    except Exception as e:
        print(f"⚠️ Fallback Marker für {pattern_name} fehlgeschlagen: {e}")


def create_pattern_summary(patterns, candle_count):
    """Create pattern analysis summary"""
    """
    Erstellt eine zusammenfassende Analyse der erkannten Patterns.

    Generiert eine übersichtliche Zusammenfassung mit:
    - Anzahl der bullish/bearish Signale
    - Durchschnittliche Signal-Stärke
    - Gesamtübersicht über erkannte Pattern-Typen

    Args:
        patterns (dict): Dictionary mit erkannten Pattern-Signalen
        candle_count (int): Anzahl der analysierten Candles

    Returns:
        html.Div: Formatiertes Pattern-Summary-Panel
    """

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
    """
    Erstellt einen Error-Chart mit Fehlermeldung.

    Zeigt eine rote Fehlermeldung in der Mitte des Charts an,
    wenn die Analyse fehlschlägt.

    Args:
        error_message (str): Anzuzeigende Fehlermeldung

    Returns:
        go.Figure: Plotly Figure mit Fehlermeldung
    """
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

# Zeit-Update Callback
@app.callback(
    Output("time-display", "children"),
    Input("clock-interval", "n_intervals")
)
def update_time(n):
    """
    Aktualisiert die Zeitanzeige in der Header-Bar.

    Wird alle 2 Sekunden ausgelöst und zeigt die aktuelle UTC-Zeit an.

    Args:
        n (int): Intervall-Counter

    Returns:
        str: Formatierte aktuelle Zeit im UTC-Format
    """
    return datetime.now().strftime("%H:%M:%S UTC")

# Exchange-Status in Echtzeit aktualisieren
@app.callback(
    [Output('exchange-status-store', 'data')] +
    [Output(f'exchange-status-{name}', 'children') for name in ['binance', 'coinbase', 'kraken', 'bybit', 'okx']],
    Input('exchange-update-interval', 'n_intervals')
)
def update_exchange_status(n):
    """Prüft auf neue Exchange-Updates aus Background-Threads
    Aktualisiert die Exchange-Status-Anzeigen in Echtzeit.

    Kommuniziert mit den Background-Threads der market_engine und
    aktualisiert die Exchange-Status-Indikatoren (online/offline/loading).

    Args:
        n (int): Intervall-Counter

    Returns:
        list: Liste mit aktualisierten Status-Store-Daten und DOM-Elementen
              für jeden Exchange-Status-Indikator
    """
    # Aktuelle Exchange-Informationen abfragen
    exchange_info = market_engine.get_exchange_info()

    # Status-Updates für jeden Exchange generieren
    outputs = []
    for name in ['binance', 'coinbase', 'kraken', 'bybit', 'okx']:
        info = exchange_info.get(name, {'status': 'offline'})

        # Visuelles Feedback basierend auf Status
        if info.get('status') == 'loading':
            status_icon = "⏳"
            status_class = "loading"
        elif info.get('status') == 'online':
            status_icon = "✅"
            status_class = "online"
        else:
            status_icon = "❌"
            status_class = "offline"

        # DOM-Element für jeweiligen Exchange aktualisieren
        outputs.append(html.Span([
            html.Span(className=f"exchange-dot {status_class}"),
            f"{name.title()}"
        ]))

    # Ersten Output für Store, restliche für Exchange-Indikatoren
    return [exchange_info] + outputs

# Exchange-Dropdown dynamisch aktualisieren, wenn neue Exchanges bereit
@app.callback(
    Output("exchange-dropdown", "options"),
    Input("exchange-status-store", "data")
)
def update_exchange_dropdown(exchange_info):
    """
    Aktualisiert die Exchange-Dropdown-Optionen basierend auf Online-Status.

    Zeigt nur Exchanges an, die erfolgreich verbunden und online sind.

    Args:
        exchange_info (dict): Aktueller Status aller Exchanges

    Returns:
        list: Liste von Dropdown-Optionen für verfügbare Exchanges
    """
    # Nur Online-Exchanges anzeigen
    online_exchanges = [name for name, info in exchange_info.items()
                        if info.get('status') == 'online']

    # Dropdown-Optionen generieren
    options = [{"label": "Auto", "value": "auto"}]
    options += [{"label": name.title(), "value": name} for name in online_exchanges]

    return options

# Market Stats Callback - Status Bar aktualisieren
@app.callback(
    [Output("market-cap-value", "children"),
     Output("volume-value", "children"),
     Output("fear-greed-value", "children"),
     Output("dominance-value", "children"),
     Output("pairs-value", "children")],
    [Input("clock-interval", "n_intervals")]
)
def update_market_stats(n):
    """
    Aktualisiert die Marktstatistiken in der Status-Bar.

    Wird alle 2 Sekunden ausgelöst und holt aktuelle Marktdaten
    aus der market_engine.

    Args:
        n (int): Intervall-Counter

    Returns:
        list: Liste mit formatierten Werten für alle Status-Bar-Metriken
    """
    stats = market_engine.get_market_stats()
    return [
        stats['market_cap'],
        stats['volume_24h'],
        stats['fear_greed'],
        stats['btc_dominance'],
        stats['active_pairs']
    ]
# endregion

if __name__ == '__main__':
    """
    Startet den Dash-Server für das Pattern Pilot Terminal.

    Konfiguriert für lokalen Zugriff auf Port 8050 mit deaktiviertem
    Debug-Modus für Produktionsumgebungen.
    """
    app.run(debug=False, host='127.0.0.1', port=8050)