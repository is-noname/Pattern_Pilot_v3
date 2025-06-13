#!/usr/bin/env python3
"""
🎯 Pattern Test Interactive
Datei: /core/patterns/test_pattern_interactive.py

Testet Pattern Detection + Rendering mit interaktiver Auswahl
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os

# •••••••••••••••••••••••••• System Setup •••••••••••••••••••••••••• #
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.append(project_root)

from core.patterns.chart_patterns import PATTERN_DETECTORS, PATTERN_RENDERERS


# •••••••••••••••••••••••••• Pattern-Specific Test Data Generators •••••••••••••••••••••••••• #

def create_double_bottom_data():
    """🔻 Double Bottom: Zwei Tiefs auf ähnlichem Level"""
    days = 100
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    # Base trend
    base_price = 100
    close = [base_price + i * 0.3 + np.random.normal(0, 1.5) for i in range(days)]
    
    # Erstes Bottom (Tag 25-35)
    for i in range(25, 35):
        close[i] = base_price - 12 + abs(i - 30) * 0.8
    
    # Zweites Bottom (Tag 65-75) 
    for i in range(65, 75):
        close[i] = base_price - 11 + abs(i - 70) * 0.8
        
    return create_ohlcv_from_close(dates, close)

def create_head_shoulders_data():
    """👤 Head & Shoulders: Links-Schulter, Kopf, Rechts-Schulter"""
    days = 120
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    base_price = 100
    close = [base_price + np.random.normal(0, 2) for _ in range(days)]
    
    # Linke Schulter (Tag 20-30)
    for i in range(20, 30):
        close[i] = base_price + 15 - abs(i - 25) * 1.5
    
    # Kopf (Tag 50-60) - höher als Schultern
    for i in range(50, 60):
        close[i] = base_price + 25 - abs(i - 55) * 2
    
    # Rechte Schulter (Tag 80-90)  
    for i in range(80, 90):
        close[i] = base_price + 16 - abs(i - 85) * 1.5
        
    return create_ohlcv_from_close(dates, close)

def create_ascending_triangle_data():
    """📈 Ascending Triangle: Horizontaler Widerstand + ansteigende Unterstützung"""
    days = 80
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    base_price = 100
    close = []
    
    # Horizontaler Widerstand bei 120
    resistance = 120
    
    for i in range(days):
        # Ansteigende Unterstützung
        support = base_price + (i / days) * 15
        
        # Oszillation zwischen Support und Resistance mit ansteigender Tendenz
        if i % 15 < 8:  # Aufwärtsbewegung zu Resistance
            price = support + (resistance - support) * (i % 15) / 8
        else:  # Rückzug zu Support
            price = resistance - (resistance - support) * ((i % 15) - 8) / 7
            
        close.append(price + np.random.normal(0, 1))
        
    return create_ohlcv_from_close(dates, close)

def create_bullish_flag_data():
    """🚩 Bullish Flag: Steiler Anstieg + kleine Konsolidierung"""
    days = 60
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    base_price = 100
    close = []
    
    for i in range(days):
        if i < 15:  # Steiler Anstieg (Flaggenmast)
            price = base_price + i * 3
        elif i < 45:  # Kleine Konsolidierung (Flagge)
            price = base_price + 15 * 3 - (i - 15) * 0.3
        else:  # Ausbruch
            price = base_price + 15 * 3 - 30 * 0.3 + (i - 45) * 2
            
        close.append(price + np.random.normal(0, 1.5))
        
    return create_ohlcv_from_close(dates, close)

def create_falling_wedge_data():
    """📉 Falling Wedge: Fallende Widerstände und Unterstützungen, aber konvergierend"""
    days = 70
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    base_price = 120
    close = []
    
    for i in range(days):
        # Fallende aber konvergierende Trendlinien
        upper = base_price - i * 0.5  # Obere Trendlinie
        lower = base_price - i * 0.8 - 10  # Untere Trendlinie (steiler fallend)
        
        # Oszillation zwischen den Linien
        oscillation = np.sin(i * 0.3) * 0.3 + 0.5  # 0-1 range
        price = lower + (upper - lower) * oscillation
        
        close.append(price + np.random.normal(0, 1))
        
    return create_ohlcv_from_close(dates, close)

def create_cup_handle_data():
    """☕ Cup & Handle: U-förmige Basis + kleiner Handle"""
    days = 100
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    base_price = 100
    close = []
    
    for i in range(days):
        if i < 60:  # Cup formation (U-shape)
            # Parabel für Cup
            cup_progress = i / 60
            cup_depth = -20 * (4 * cup_progress * (1 - cup_progress))  # Parabel
            price = base_price + cup_depth
        elif i < 85:  # Handle (kleine Abwärtskorrektur)
            handle_progress = (i - 60) / 25
            price = base_price - handle_progress * 8
        else:  # Breakout
            price = base_price + (i - 85) * 1.5
            
        close.append(price + np.random.normal(0, 1.5))
        
    return create_ohlcv_from_close(dates, close)

def create_generic_data():
    """🎲 Generic: Zufällige Bewegungen für andere Patterns"""
    days = 80
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    base_price = 100
    close = [base_price]
    
    for i in range(1, days):
        # Random walk mit leichter Aufwärtstendenz
        change = np.random.normal(0.1, 2)
        close.append(close[-1] + change)
        
    return create_ohlcv_from_close(dates, close)

def create_ohlcv_from_close(dates, close_prices):
    """Helper: Erstellt vollständiges OHLCV DataFrame aus Close-Preisen"""
    df = pd.DataFrame({'date': dates, 'close': close_prices})
    
    # OHLV ableiten
    df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0.2, 2, len(df))
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0.2, 2, len(df))
    df['volume'] = np.random.uniform(1000, 5000, len(df))
    
    # Ensure high >= max(open,close) and low <= min(open,close)
    df['high'] = np.maximum(df['high'], df[['open', 'close']].max(axis=1))
    df['low'] = np.minimum(df['low'], df[['open', 'close']].min(axis=1))
    
    return df


# •••••••••••••••••••••••••• Pattern-Specific Data Mapping •••••••••••••••••••••••••• #

PATTERN_DATA_GENERATORS = {
    'double_bottom': create_double_bottom_data,
    'double_top': lambda: create_double_bottom_data(),  # Kann invertiert werden
    'head_and_shoulders': create_head_shoulders_data,
    'inverse_head_and_shoulders': lambda: create_head_shoulders_data(),  # Kann invertiert werden
    'ascending_triangle': create_ascending_triangle_data,
    'bullish_flag': create_bullish_flag_data,
    'falling_wedge': create_falling_wedge_data,
    'cup_and_handle': create_cup_handle_data,
    # Für alle anderen Patterns
    'default': create_generic_data
}


# •••••••••••••••••••••••••• Interactive Pattern Selection •••••••••••••••••••••••••• #

def show_pattern_menu():
    """Zeigt alle verfügbaren Patterns in nummerierter Liste"""
    print("\n" + "="*70)
    print("🎯 PATTERN TEST INTERACTIVE")
    print("="*70)
    
    pattern_list = list(PATTERN_DETECTORS.keys())
    
    print(f"\n📋 Verfügbare Patterns ({len(pattern_list)}):")
    print("-" * 50)
    
    # Gruppierung für bessere Übersicht
    categories = {
        'Reversal': ['double_bottom', 'double_top', 'head_and_shoulders', 'inverse_head_and_shoulders', 
                    'triple_top', 'triple_bottom', 'rounding_bottom', 'rounding_top', 'v_pattern'],
        'Triangle': ['ascending_triangle', 'descending_triangle', 'symmetrical_triangle'],
        'Continuation': ['bullish_flag', 'bearish_flag', 'bullish_pennant', 'bearish_pennant',
                        'bullish_rectangle', 'bearish_rectangle'],
        'Channel': ['upward_channel', 'downward_channel'],
        'Wedge': ['falling_wedge', 'rising_wedge'],
        'Gap': ['breakaway_gap', 'runaway_gap', 'exhaustion_gap', 'common_gap'],
        'Complex': ['cup_and_handle', 'diamond_top', 'diamond_bottom']
    }
    
    pattern_index = 1
    for category, patterns in categories.items():
        print(f"\n🔖 {category}:")
        for pattern in patterns:
            if pattern in pattern_list:
                print(f"  {pattern_index:2d}. {pattern.replace('_', ' ').title()}")
                pattern_index += 1
    
    # Remaining patterns
    categorized = set()
    for patterns in categories.values():
        categorized.update(patterns)
    
    remaining = [p for p in pattern_list if p not in categorized]
    if remaining:
        print(f"\n🔖 Other:")
        for pattern in remaining:
            print(f"  {pattern_index:2d}. {pattern.replace('_', ' ').title()}")
            pattern_index += 1
    
    print(f"\n  {pattern_index:2d}. 🎲 ALL PATTERNS (Test alle)")
    print(f"   0. ❌ EXIT")
    
    return pattern_list

def get_user_choice(pattern_list):
    """Holt Benutzer-Auswahl"""
    total_options = len(pattern_list) + 2  # +1 für ALL, +1 für EXIT
    
    while True:
        try:
            choice = input(f"\n👆 Wähle Pattern (1-{total_options-1}, 0=Exit): ").strip()
            
            if choice == '0':
                return None
            
            choice_num = int(choice)
            
            if choice_num == total_options - 1:  # ALL PATTERNS
                return 'ALL'
            
            if 1 <= choice_num <= len(pattern_list):
                return pattern_list[choice_num - 1]
            else:
                print(f"❌ Ungültige Auswahl. Bitte 1-{total_options-1} oder 0 eingeben.")
                
        except ValueError:
            print("❌ Bitte eine Zahl eingeben.")

def generate_test_data(pattern_name):
    """Generiert pattern-spezifische Testdaten"""
    generator = PATTERN_DATA_GENERATORS.get(pattern_name, PATTERN_DATA_GENERATORS['default'])
    return generator()


# •••••••••••••••••••••••••• Pattern Testing Engine •••••••••••••••••••••••••• #

def test_single_pattern(pattern_name):
    """Testet ein einzelnes Pattern"""
    print(f"\n🔍 Testing Pattern: {pattern_name.replace('_', ' ').title()}")
    print("-" * 60)
    
    # 1. Testdaten generieren
    print("📊 Generiere Testdaten...")
    test_data = generate_test_data(pattern_name)
    print(f"✅ {len(test_data)} Datenpunkte erstellt")
    
    # 2. DataFrame für Pattern Detection vorbereiten
    from core.patterns.chart_patterns import prepare_dataframe_for_patterns
    prepared_data = prepare_dataframe_for_patterns(test_data)
    
    # 3. Pattern Detection
    print("🔍 Pattern Detection läuft...")
    detector_func = PATTERN_DETECTORS[pattern_name]
    try:
        detected_patterns = detector_func(prepared_data, config=None, timeframe="1d")
        print(f"✅ {len(detected_patterns)} Pattern-Instanzen gefunden")
        
        # Pattern Details ausgeben
        if detected_patterns:
            for i, pattern in enumerate(detected_patterns, 1):
                print(f"\n📋 Pattern #{i} Details:")
                for key, value in pattern.items():
                    if key not in ['data_points', 'raw_data']:  # Große Daten ausblenden
                        print(f"   {key}: {value}")
        else:
            print("⚠️ Keine Pattern-Instanzen erkannt")
            
    except Exception as e:
        print(f"❌ Pattern Detection fehlgeschlagen: {e}")
        detected_patterns = []
    
    # 4. Pattern Rendering (falls Pattern gefunden)
    if detected_patterns and pattern_name in PATTERN_RENDERERS:
        print("\n🎨 Pattern Rendering...")
        try:
            renderer_func = PATTERN_RENDERERS[pattern_name]
            
            # Erstelle Plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Basechart (Candlestick-ähnlich)
            ax.plot(range(len(test_data)), test_data['close'], label='Close Price', linewidth=1.5)
            ax.fill_between(range(len(test_data)), test_data['low'], test_data['high'], 
                           alpha=0.3, label='High-Low Range')
            
            # Pattern Rendering hinzufügen
            renderer_func(ax, detected_patterns[0], test_data)  # Erstes Pattern rendern
            
            ax.set_title(f"{pattern_name.replace('_', ' ').title()} - Test Chart")
            ax.set_xlabel("Time")
            ax.set_ylabel("Price")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
            print("✅ Chart angezeigt")
            
        except Exception as e:
            print(f"⚠️ Pattern Rendering fehlgeschlagen: {e}")
    
    return len(detected_patterns) > 0

def test_all_patterns():
    """Testet alle verfügbaren Patterns"""
    print(f"\n🎯 TESTING ALL {len(PATTERN_DETECTORS)} PATTERNS")
    print("=" * 70)
    
    results = {}
    successful = 0
    
    for i, pattern_name in enumerate(PATTERN_DETECTORS.keys(), 1):
        print(f"\n[{i}/{len(PATTERN_DETECTORS)}] {pattern_name}")
        
        try:
            success = test_single_pattern(pattern_name)
            results[pattern_name] = 'SUCCESS' if success else 'NO_PATTERNS'
            if success:
                successful += 1
        except Exception as e:
            results[pattern_name] = f'ERROR: {str(e)[:50]}'
            print(f"❌ Test fehlgeschlagen: {e}")
    
    # Zusammenfassung
    print(f"\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Erfolgreiche Pattern: {successful}/{len(PATTERN_DETECTORS)}")
    
    print(f"\n📋 Details:")
    for pattern, result in results.items():
        status_emoji = "✅" if result == 'SUCCESS' else "⚠️" if result == 'NO_PATTERNS' else "❌"
        print(f"  {status_emoji} {pattern}: {result}")


# •••••••••••••••••••••••••• Main Test Loop •••••••••••••••••••••••••• #

def main():
    """Hauptprogramm mit interaktiver Pattern-Auswahl"""
    while True:
        pattern_list = show_pattern_menu()
        choice = get_user_choice(pattern_list)
        
        if choice is None:  # EXIT
            print("\n👋 Auf Wiedersehen!")
            break
        elif choice == 'ALL':  # Alle Patterns testen
            test_all_patterns()
        else:  # Einzelnes Pattern
            test_single_pattern(choice)
        
        # Weiter? 
        continue_test = input("\n❓ Weiteren Test starten? (y/n): ").strip().lower()
        if continue_test not in ['y', 'yes', 'j', 'ja']:
            print("\n👋 Auf Wiedersehen!")
            break


if __name__ == "__main__":
    main()
