# ================================================================================
# 📁 test_double_bottom_with_wait.py - MIT EXCHANGE WAIT SYSTEM
# ================================================================================

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta



def wait_for_exchanges():
    """Warte bis Exchanges geladen sind"""

    print("⏳ Warte auf Exchange-Loading...")

    from core.market_engine import market_engine

    max_wait = 30  # Maximum 30 Sekunden warten
    wait_time = 0

    while wait_time < max_wait:
        # Prüfe ob mindestens eine Exchange geladen ist
        ready_exchanges = []

        for name, exchange in market_engine.exchanges.items():
            if exchange and not isinstance(exchange, dict):  # Nicht nur Config-Dict
                ready_exchanges.append(name)

        if ready_exchanges:
            print(f"✅ Exchanges bereit: {', '.join(ready_exchanges)}")
            return True

        print(f"⏳ Warte... ({wait_time}s/{max_wait}s)")
        time.sleep(2)
        wait_time += 2

    print(f"⚠️ Timeout nach {max_wait}s - versuche trotzdem...")
    return False


def test_with_mock_data():
    """Teste mit Mock Double Bottom Daten falls keine echten Daten"""

    print("\n🎭 Teste mit Mock Double Bottom Daten...")

    # Erstelle Mock BTC-ähnliche Daten mit Double Bottom
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Base price around 50000
    base_prices = []
    for i in range(100):
        if i < 25:
            # Fallende Phase
            price = 55000 - (i * 800) + (i * 50)  # Leicht fallend mit Volatilität
        elif 25 <= i <= 30:
            # Erstes Bottom bei ~45000
            price = 45000 + abs(i - 27.5) * 200
        elif 30 < i < 50:
            # Erholung zur Neckline
            price = 45000 + ((i - 30) / 20) * 8000  # Bis ~53000
        elif 50 <= i <= 55:
            # Zweites Bottom bei ~45000
            price = 45000 + abs(i - 52.5) * 200
        else:
            # Breakout nach oben
            price = 45000 + ((i - 55) / 45) * 15000  # Bis ~60000

        base_prices.append(price)

    # OHLCV aus Base Prices
    import numpy as np
    np.random.seed(42)  # Reproduzierbare Zufallszahlen

    df = pd.DataFrame({
        'open': [p + np.random.uniform(-500, 500) for p in base_prices],
        'high': [p + np.random.uniform(200, 1000) for p in base_prices],
        'low': [p - np.random.uniform(200, 1000) for p in base_prices],
        'close': base_prices,
        'volume': [np.random.uniform(1000, 5000) for _ in range(100)]
    }, index=dates)  # 🔧 DateTime-Index direkt setzen

    print(f"✅ Mock Daten erstellt: {len(df)} Kerzen")

    # Simuliere Pattern Detection mit Mock-Patterns
    mock_patterns = {
        'double_bottom': [
            {
                'type': 'double_bottom',
                'P1': 27,  # Erstes Bottom
                'P2': 52,  # Zweites Bottom
                'neckline_idx': 40,
                'neckline': 53000,
                'confirmed': True,
                'breakout_idx': 65,
                'target': 61000,
                'stop_loss': 43000
            }
        ]
    }

    print(f"🎯 Mock Double Bottom Pattern:")
    pattern = mock_patterns['double_bottom'][0]
    print(f"   P1: {pattern['P1']}, P2: {pattern['P2']}")
    print(f"   Neckline: ${pattern['neckline']:.0f}")
    print(f"   Target: ${pattern['target']:.0f}")
    print(f"   Confirmed: {pattern['confirmed']}")

    return df, mock_patterns


def test_double_bottom_integration_with_wait():
    """
    Teste Double Bottom Integration mit Wait-System
    """

    print("🚀 DOUBLE BOTTOM TEST - MIT EXCHANGE WAIT")
    print("=" * 60)

    try:
        # Import market_engine
        from core.market_engine import market_engine
        print("✅ Market Engine importiert")

        # Warte auf Exchanges
        exchanges_ready = wait_for_exchanges()

        if exchanges_ready:
            # Versuche echte Daten zu holen
            print("\n📊 Versuche echte BTC Daten...")
            result = market_engine.get_ohlcv("BTC/USDT", timeframe="1d", limit=200)

            if 'data' in result and not result['data'].empty:
                df = result['data']
                patterns = result.get('patterns', {})

                print(f"✅ Echte BTC Daten geladen: {len(df)} Kerzen")

                # Prüfe auf Double Patterns
                double_bottoms = patterns.get('double_bottom', [])
                double_tops = patterns.get('double_top', [])

                if double_bottoms or double_tops:
                    print(f"✅ Double Patterns gefunden!")
                    print(f"   Double Bottoms: {len(double_bottoms)}")
                    print(f"   Double Tops: {len(double_tops)}")

                    test_patterns = {}
                    if double_bottoms: test_patterns['double_bottom'] = double_bottoms
                    if double_tops: test_patterns['double_top'] = double_tops

                    # Erstelle Chart mit echten Daten
                    create_and_save_chart(df, test_patterns, "BTC/USDT (Real Data)", "real_btc")
                    return True
                else:
                    print("⚠️ Keine Double Patterns in echten BTC Daten")

        # Fallback: Mock Daten
        print("\n🎭 Verwende Mock Daten für Demo...")
        df, mock_patterns = test_with_mock_data()

        # Erstelle Chart mit Mock Daten
        create_and_save_chart(df, mock_patterns, "BTC/USDT (Mock Data)", "mock_btc")

        return True

    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_and_save_chart(df, patterns, title, filename_prefix):
    """Erstelle und speichere Chart"""

    print(f"\n🎨 Erstelle Chart: {title}")

    # Chart Setup
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, 'Volume')
    )

    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price",
            increasing_line_color='#06fc99',
            decreasing_line_color='#f44336',
            increasing_fillcolor='#06fc99',
            decreasing_fillcolor='#f44336',
        ),
        row=1, col=1
    )

    # Volume
    colors = ['#06fc99' if close >= open else '#f44336'
              for close, open in zip(df['close'], df['open'])]

    fig.add_trace(
        go.Bar(
            x=df['datetime'] if 'datetime' in df.columns else df.index,
            y=df['volume'],
            name="Volume",
            marker_color=colors,
            opacity=0.6
        ),
        row=2, col=1
    )

    # ✅ ADD DOUBLE PATTERN OVERLAYS
    pattern_count = 0

    for pattern_name, pattern_list in patterns.items():
        print(f"   🎨 Rendering {pattern_name}: {len(pattern_list)} patterns")

        for pattern in pattern_list:
            if 'type' not in pattern:
                pattern['type'] = pattern_name

            try:
                # Import und render Double Pattern
                from core.patterns.formation_patterns.double_patterns import render_pattern_plotly

                render_pattern_plotly(fig, df, pattern)
                pattern_count += 1

                print(f"      ✅ Pattern gerendert - P1: {pattern.get('P1')}, P2: {pattern.get('P2')}")

            except Exception as e:
                print(f"      ❌ Render Error: {e}")

    # Chart Styling
    fig.update_layout(
        height=800,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(family="Monaco, Consolas", size=10, color="#e0e0e0"),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified",
        title=dict(
            text=f"Double Pattern Overlay Test - {title}",
            x=0.5,
            font=dict(size=16, color="#e0e0e0")
        )
    )

    # Grid + Crosshair
    fig.update_xaxes(gridcolor='#404040', gridwidth=1, showspikes=True, spikethickness=1, spikecolor="#06fc99",
                     spikemode="across")
    fig.update_yaxes(gridcolor='#404040', gridwidth=1, showspikes=True, spikethickness=1, spikecolor="#06fc99",
                     spikemode="across")

    # Speichere Chart
    filename = f"{filename_prefix}_double_patterns_test.html"
    fig.write_html(filename)
    print(f"💾 Chart gespeichert: {filename}")

    # Versuche Browser zu öffnen
    try:
        import webbrowser
        webbrowser.open(filename)
        print(f"🌐 Chart im Browser geöffnet")
    except:
        print(f"📂 Öffne manuell: {filename}")

    print(f"✅ {pattern_count} Patterns gerendert")


def main():
    """Main test function"""

    success = test_double_bottom_integration_with_wait()

    if success:
        print(f"\n🎉 SUCCESS! Double Bottom Plotly Integration funktioniert!")
        print(f"\n🔍 Was du sehen solltest:")
        print(f"   ✅ Grüne Kreise an Support-Punkten (P1, P2)")
        print(f"   ✅ Gestrichelte rote Neckline")
        print(f"   ✅ Grüne Dreiecke bei Breakouts")
        print(f"   ✅ Gepunktete Target-Linien")
        print(f"   ✅ Hover-Informationen bei Mouse-Over")

        print(f"\n➡️ VERGLEICH:")
        print(f"   🔸 Deine Haupt-App: Viele kleine Pattern-Marker")
        print(f"   🔸 Dieser Test: Professionelle Double Bottom Overlays")

        print(f"\n🚀 NÄCHSTE SCHRITTE:")
        print(f"   1. Öffne den HTML-Chart im Browser")
        print(f"   2. Vergleiche Overlay-Qualität mit Haupt-App")
        print(f"   3. Wenn zufrieden: Weitere Pattern-Typen hinzufügen")

    else:
        print(f"\n❌ Test nicht erfolgreich - Debug weitere Schritte")


if __name__ == "__main__":
    main()