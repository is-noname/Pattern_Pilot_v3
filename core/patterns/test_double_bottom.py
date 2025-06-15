# ================================================================================
# 🔧 FIXED DOUBLE BOTTOM TEST - Garantierte Pattern Detection
# ================================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ================================================================================
# 🎯 PERFEKTE TESTDATEN - Garantiert Double Bottom
# ================================================================================

def create_perfect_double_bottom():
    """Erstellt perfekte Double Bottom Testdaten"""

    print("🎯 Erstelle PERFEKTE Double Bottom Testdaten...")

    # Weniger Datenpunkte, clearer Pattern
    days = 60
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    dates.reverse()

    # Basis-Preis: 100
    base_price = 100
    close = []

    for i in range(days):
        if i < 15:
            # Anfangsphase: leicht fallend
            price = base_price - (i * 2) + np.random.normal(0, 0.5)
        elif 15 <= i <= 20:
            # ERSTES BOTTOM: exakt bei 70
            price = 70 + np.random.normal(0, 0.3)
        elif 20 < i < 35:
            # Zwischenphase: steigt zur Neckline
            progress = (i - 20) / 15  # 0 bis 1
            price = 70 + (progress * 20) + np.random.normal(0, 0.5)  # 70 bis 90
        elif 35 <= i <= 40:
            # ZWEITES BOTTOM: exakt bei 70 (gleiche Höhe!)
            price = 70 + np.random.normal(0, 0.3)
        else:
            # Nach dem zweiten Bottom: Breakout
            progress = (i - 40) / 20  # 0 bis 1
            price = 70 + (progress * 25) + np.random.normal(0, 0.5)  # 70 bis 95+

        close.append(max(50, price))  # Minimum 50 für Realismus

    # OHLCV basierend auf Close
    high = [c + np.random.uniform(0.2, 1.0) for c in close]
    low = [c - np.random.uniform(0.2, 1.0) for c in close]
    open_price = [c + np.random.uniform(-0.5, 0.5) for c in close]
    volume = [1000 + np.random.uniform(0, 200) for _ in range(days)]

    df = pd.DataFrame({
        'date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    print(f"✅ Perfekte Testdaten erstellt: {len(df)} Datenpunkte")
    print(f"   Erstes Bottom um Index 17-18 bei ~70")
    print(f"   Zweites Bottom um Index 37-38 bei ~70")
    print(f"   Neckline bei ~90")

    return df


# ================================================================================
# 🔧 DEBUG: Pattern Detection Parameter
# ================================================================================

def debug_pattern_detection(df):
    """Debug Pattern Detection mit verschiedenen Parametern"""

    print("\n🔍 DEBUG: Pattern Detection...")

    # Teste verschiedene Parameter-Sets
    test_configs = [
        {"tolerance": 0.05, "lookback_periods": 3, "min_pattern_bars": 3},  # Sehr locker
        {"tolerance": 0.03, "lookback_periods": 5, "min_pattern_bars": 5},  # Standard
        {"tolerance": 0.02, "lookback_periods": 7, "min_pattern_bars": 7},  # Streng
    ]

    for i, config in enumerate(test_configs, 1):
        print(f"\n   Test {i}: tolerance={config['tolerance']}, lookback={config['lookback_periods']}")

        try:
            from core.patterns.formation_patterns.double_patterns import detect_double_bottom

            patterns = detect_double_bottom(df, config=config)

            if patterns:
                print(f"   ✅ {len(patterns)} Pattern(s) gefunden!")
                pattern = patterns[0]
                print(f"      P1: {pattern['P1']}, P2: {pattern['P2']}")
                print(f"      Confirmed: {pattern['confirmed']}")
                return df, patterns
            else:
                print(f"   ❌ Keine Patterns mit diesen Parametern")

        except Exception as e:
            print(f"   ❌ Fehler: {e}")

    return df, []


# ================================================================================
# 🔍 MANUAL DEBUG: Schritt-für-Schritt
# ================================================================================

def manual_debug_detection(df):
    """Manuelle Debug-Analyse der Pattern Detection"""

    print("\n🔍 MANUAL DEBUG...")

    # Zeige Daten-Übersicht
    print(f"DataFrame Info:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Low values range: {df['low'].min():.2f} - {df['low'].max():.2f}")

    # Finde lokale Tiefs manuell
    lows = df['low'].values
    lookback = 3

    bottoms = []
    for i in range(lookback, len(lows) - lookback):
        prev = np.min(lows[i - lookback:i])
        next_ = np.min(lows[i + 1:i + lookback + 1])
        if lows[i] < prev and lows[i] < next_:
            bottoms.append((i, lows[i]))

    print(f"\n   Gefundene lokale Tiefs: {len(bottoms)}")
    for idx, (i, price) in enumerate(bottoms):
        print(f"      #{idx + 1}: Index {i}, Price {price:.2f}")

    # Prüfe paarweise auf Double Bottom
    if len(bottoms) >= 2:
        for i in range(len(bottoms) - 1):
            idx1, price1 = bottoms[i]
            idx2, price2 = bottoms[i + 1]

            distance = idx2 - idx1
            price_diff = abs(price1 - price2) / price1

            print(f"\n   Paar {i + 1}: Index {idx1} ({price1:.2f}) + Index {idx2} ({price2:.2f})")
            print(f"      Abstand: {distance} Kerzen")
            print(f"      Preis-Diff: {price_diff:.3f} ({price_diff * 100:.1f}%)")

            if distance >= 5 and price_diff <= 0.05:
                print(f"      ✅ Potentielles Double Bottom!")
                return True

    return False


# ================================================================================
# 🧪 ERWEITERTE TESTS
# ================================================================================

def test_with_perfect_data():
    """Test mit perfekten Daten"""

    print("🧪 TEST 1: Perfekte Double Bottom Daten")
    print("=" * 50)

    # Perfekte Testdaten
    df = create_perfect_double_bottom()

    # Manual Debug
    manual_found = manual_debug_detection(df)

    if manual_found:
        print("\n✅ Manuell gefunden - teste Pattern Detection...")

        # Pattern Detection mit Debug
        df, patterns = debug_pattern_detection(df)

        if patterns:
            print("\n🎉 SUCCESS! Pattern Detection funktioniert!")
            return df, patterns
        else:
            print("\n⚠️ Pattern Detection findet nichts - Parameter zu streng?")

    return df, []


def test_with_simple_data():
    """Test mit noch einfacheren Daten"""

    print("\n🧪 TEST 2: Super Simple Daten")
    print("=" * 50)

    # ULTRA-einfache Testdaten
    prices = [100, 95, 90, 85, 80, 75, 70, 75, 80, 85, 90, 95, 85, 80, 75, 70, 75, 80, 85, 90, 95, 100]

    df = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=len(prices)),
        'open': [p + np.random.uniform(-1, 1) for p in prices],
        'high': [p + np.random.uniform(1, 3) for p in prices],
        'low': [p - np.random.uniform(1, 3) for p in prices],
        'close': prices,
        'volume': [1000] * len(prices)
    })

    print(f"✅ Ultra-Simple Daten: {len(df)} Punkte")
    print(f"   Bottoms bei Index ~6 und ~15 (beide bei ~70)")

    # Test
    df, patterns = debug_pattern_detection(df)

    return df, patterns


# ================================================================================
# 🚀 MAIN TEST RUNNER
# ================================================================================

def run_fixed_tests():
    """Führe erweiterte Tests aus"""

    print("🚀 FIXED DOUBLE BOTTOM TEST SUITE")
    print("=" * 60)

    # Test 1: Perfekte Daten
    df, patterns = test_with_perfect_data()

    if patterns:
        print("\n✅ TEST 1 ERFOLGREICH!")
        test_dispatchers(df, patterns)
        return True

    # Test 2: Ultra-Simple Daten
    df, patterns = test_with_simple_data()

    if patterns:
        print("\n✅ TEST 2 ERFOLGREICH!")
        test_dispatchers(df, patterns)
        return True

    # Test 3: Parameter-Problem?
    print("\n🔧 TEST 3: Parameter Check")
    check_detection_function()

    return False


def test_dispatchers(df, patterns):
    """Teste Dispatcher nach erfolgreicher Detection"""

    print("\n🎯 Testing Dispatchers...")

    pattern = patterns[0]

    # Matplotlib Test
    try:
        from core.patterns.formation_patterns.double_patterns import render_pattern
        print("✅ Matplotlib Dispatcher verfügbar")
    except ImportError as e:
        print(f"❌ Matplotlib Dispatcher fehlt: {e}")

    # Plotly Test
    try:
        from core.patterns.formation_patterns.double_patterns import render_pattern_plotly
        print("✅ Plotly Dispatcher verfügbar")

        # Quick Plotly Test
        import plotly.graph_objects as go
        fig = go.Figure()
        render_pattern_plotly(fig, df, pattern)
        print("✅ Plotly Rendering funktioniert!")

    except ImportError as e:
        print(f"❌ Plotly Dispatcher fehlt: {e}")
    except Exception as e:
        print(f"❌ Plotly Rendering Fehler: {e}")


def check_detection_function():
    """Prüfe die Detection Function selbst"""

    try:
        from core.patterns.formation_patterns.double_patterns import detect_double_bottom
        print("✅ detect_double_bottom importierbar")

        # Teste mit minimalen Daten
        minimal_df = pd.DataFrame({
            'open': [100, 90, 80, 70, 80, 90, 80, 70, 80, 90],
            'high': [105, 95, 85, 75, 85, 95, 85, 75, 85, 95],
            'low': [95, 85, 75, 65, 75, 85, 75, 65, 75, 85],
            'close': [100, 90, 80, 70, 80, 90, 80, 70, 80, 90],
            'volume': [1000] * 10
        })

        result = detect_double_bottom(minimal_df)
        print(f"✅ Function call successful, returned: {type(result)}")

    except Exception as e:
        print(f"❌ Detection Function Problem: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_fixed_tests()