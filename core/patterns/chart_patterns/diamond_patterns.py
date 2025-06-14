import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT DIAMOND PATTERNS
# ==============================================================================
def detect_diamond_top(df, config=None, timeframe="1d"):
    """
    Erkennt Diamond-Top-Muster (bearishes Umkehrmuster)
    
    Eigenschaften:
    - Kombination aus erweiterndem und dann verengendem Muster
    - Rautenförmige Erscheinung im Chart
    - Typischerweise an Markthöchstständen zu finden
    - Besteht aus einer Erweiterung gefolgt von einer Verengung
    """
    # Config laden
    if config is None:
        config = PATTERN_CONFIGS.get("diamond_top", {})
    
    min_pattern_bars = config.get("min_pattern_bars", 15)
    max_pattern_bars = config.get("max_pattern_bars", 60)
    min_width = config.get("min_width", 0.05)  # Mindestbreite des Diamanten als Prozent des Preises
    
    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten
    
    patterns = []
    
    # Für verschiedene potenzielle Diamantmuster
    step_size = max(1, min(20, len(df) // 10))  # Reduziert die Anzahl der zu prüfenden Startpunkte
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length
            
            if end_idx >= len(df):
                continue
            
            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            
            # Ein Diamond-Top besteht aus einer Erweiterung gefolgt von einer Verengung
            # Wir teilen das Segment in zwei Hälften
            mid_idx = i + pattern_length // 2
            
            # Erste Hälfte (Erweiterung) - Broadening Pattern
            first_half = df.iloc[i:mid_idx + 1]
            # Zweite Hälfte (Verengung) - Triangle Pattern
            second_half = df.iloc[mid_idx:end_idx + 1]
            
            if len(first_half) < 5 or len(second_half) < 5:
                continue
            
            # Analysiere die erste Hälfte auf Erweiterung
            first_half_highs = first_half['high'].values
            first_half_lows = first_half['low'].values
            
            # Berechne Höhen- und Tief-Trendlinien für die erste Hälfte
            try:
                x1 = np.arange(len(first_half_highs))
                first_high_slope, first_high_intercept = np.polyfit(x1, first_half_highs, 1)
                
                x2 = np.arange(len(first_half_lows))
                first_low_slope, first_low_intercept = np.polyfit(x2, first_half_lows, 1)
            except:
                continue
            
            # Für Erweiterung: Hochs steigen stärker als Tiefs oder Tiefs fallen stärker als Hochs
            if not ((first_high_slope > 0 and first_low_slope < 0) or 
                   (first_high_slope > first_low_slope and first_low_slope >= 0) or
                   (first_high_slope <= 0 and first_low_slope < first_high_slope)):
                continue
            
            # Analysiere die zweite Hälfte auf Verengung
            second_half_highs = second_half['high'].values
            second_half_lows = second_half['low'].values
            
            # Berechne Höhen- und Tief-Trendlinien für die zweite Hälfte
            try:
                x3 = np.arange(len(second_half_highs))
                second_high_slope, second_high_intercept = np.polyfit(x3, second_half_highs, 1)
                
                x4 = np.arange(len(second_half_lows))
                second_low_slope, second_low_intercept = np.polyfit(x4, second_half_lows, 1)
            except:
                continue
            
            # Für Verengung: Hochs fallen oder steigen langsamer, Tiefs steigen oder fallen langsamer
            if not ((second_high_slope < 0 and second_low_slope > 0) or
                   (second_high_slope > 0 and second_low_slope > 0 and second_high_slope < second_low_slope) or
                   (second_high_slope < 0 and second_low_slope < 0 and second_high_slope > second_low_slope)):
                continue
            
            # Berechne die Diamantbreite am breitesten Punkt
            # Breite am Ende der ersten Hälfte / Anfang der zweiten Hälfte
            mid_high = first_high_intercept + first_high_slope * (len(first_half) - 1)
            mid_low = first_low_intercept + first_low_slope * (len(first_half) - 1)
            
            diamond_width = (mid_high - mid_low) / ((mid_high + mid_low) / 2)
            
            if diamond_width < min_width:
                continue
            
            # Suche nach Durchbruch nach unten an unterer Trendlinie
            confirmed = False
            breakout_idx = None
            
            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                # Projizierte untere Trendlinie am Ende des Diamanten
                projected_low = second_low_intercept + second_low_slope * (len(second_half) - 1)
                
                if df['close'].iloc[j] < projected_low * 0.98:  # 2% Durchbruch nach unten
                    confirmed = True
                    breakout_idx = j
                    break
            
            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                target = None
                
                if confirmed:
                    # Kursziel: Projektion der Diamanthöhe nach unten
                    diamond_height = diamond_width * ((mid_high + mid_low) / 2)
                    target = df['close'].iloc[breakout_idx] - diamond_height
                
                patterns.append({
                    "type": "diamond_top",
                    "start_idx": i,
                    "mid_idx": mid_idx,
                    "end_idx": end_idx,
                    "width": diamond_width,
                    "first_high_slope": first_high_slope,
                    "first_high_intercept": first_high_intercept,
                    "first_low_slope": first_low_slope,
                    "first_low_intercept": first_low_intercept,
                    "second_high_slope": second_high_slope,
                    "second_high_intercept": second_high_intercept,
                    "second_low_slope": second_low_slope,
                    "second_low_intercept": second_low_intercept,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target,
                    "stop_loss": max(segment['high']) * 1.02  # 2% über dem höchsten Punkt
                })
    
    # Sortiere Muster nach Qualität
    if patterns:
        patterns.sort(key=lambda x: x["width"], reverse=True)
        return patterns[:3]  # Maximal 3 Ergebnisse
    
    return patterns


def detect_diamond_bottom(df, config=None, timeframe="1d"):
    """
    Erkennt Diamond-Bottom-Muster (bullishes Umkehrmuster)
    
    Eigenschaften:
    - Kombination aus erweiterndem und dann verengendem Muster
    - Rautenförmige Erscheinung im Chart
    - Typischerweise an Markttiefständen zu finden
    - Besteht aus einer Erweiterung gefolgt von einer Verengung
    """
    # Config laden
    if config is None:
        config = PATTERN_CONFIGS.get("diamond_bottom", {})
    
    min_pattern_bars = config.get("min_pattern_bars", 15)
    max_pattern_bars = config.get("max_pattern_bars", 60)
    min_width = config.get("min_width", 0.05)  # Mindestbreite des Diamanten als Prozent des Preises
    
    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten
    
    patterns = []
    
    # Für verschiedene potenzielle Diamantmuster
    step_size = max(1, min(20, len(df) // 10))  # Reduziert die Anzahl der zu prüfenden Startpunkte
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length
            
            if end_idx >= len(df):
                continue
            
            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            
            # Ein Diamond-Bottom besteht aus einer Erweiterung gefolgt von einer Verengung
            # Wir teilen das Segment in zwei Hälften
            mid_idx = i + pattern_length // 2
            
            # Erste Hälfte (Erweiterung) - Broadening Pattern
            first_half = df.iloc[i:mid_idx + 1]
            # Zweite Hälfte (Verengung) - Triangle Pattern
            second_half = df.iloc[mid_idx:end_idx + 1]
            
            if len(first_half) < 5 or len(second_half) < 5:
                continue
            
            # Analysiere die erste Hälfte auf Erweiterung
            first_half_highs = first_half['high'].values
            first_half_lows = first_half['low'].values
            
            # Berechne Höhen- und Tief-Trendlinien für die erste Hälfte
            try:
                x1 = np.arange(len(first_half_highs))
                first_high_slope, first_high_intercept = np.polyfit(x1, first_half_highs, 1)
                
                x2 = np.arange(len(first_half_lows))
                first_low_slope, first_low_intercept = np.polyfit(x2, first_half_lows, 1)
            except:
                continue
            
            # Für Erweiterung (umgekehrt zum Diamond Top): Hochs fallen stärker als Tiefs oder Tiefs steigen stärker als Hochs
            if not ((first_high_slope < 0 and first_low_slope > 0) or 
                   (first_high_slope < first_low_slope and first_high_slope >= 0) or
                   (first_high_slope <= 0 and first_low_slope < 0 and first_low_slope > first_high_slope)):
                continue
            
            # Analysiere die zweite Hälfte auf Verengung
            second_half_highs = second_half['high'].values
            second_half_lows = second_half['low'].values
            
            # Berechne Höhen- und Tief-Trendlinien für die zweite Hälfte
            try:
                x3 = np.arange(len(second_half_highs))
                second_high_slope, second_high_intercept = np.polyfit(x3, second_half_highs, 1)
                
                x4 = np.arange(len(second_half_lows))
                second_low_slope, second_low_intercept = np.polyfit(x4, second_half_lows, 1)
            except:
                continue
            
            # Für Verengung (umgekehrt zum Diamond Top): Hochs steigen oder fallen langsamer, Tiefs fallen oder steigen langsamer
            if not ((second_high_slope > 0 and second_low_slope < 0) or
                   (second_high_slope > 0 and second_low_slope > 0 and second_high_slope > second_low_slope) or
                   (second_high_slope < 0 and second_low_slope < 0 and second_high_slope < second_low_slope)):
                continue
            
            # Berechne die Diamantbreite am breitesten Punkt
            # Breite am Ende der ersten Hälfte / Anfang der zweiten Hälfte
            mid_high = first_high_intercept + first_high_slope * (len(first_half) - 1)
            mid_low = first_low_intercept + first_low_slope * (len(first_half) - 1)
            
            diamond_width = (mid_high - mid_low) / ((mid_high + mid_low) / 2)
            
            if diamond_width < min_width:
                continue
            
            # Suche nach Durchbruch nach oben an oberer Trendlinie
            confirmed = False
            breakout_idx = None
            
            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                # Projizierte obere Trendlinie am Ende des Diamanten
                projected_high = second_high_intercept + second_high_slope * (len(second_half) - 1)
                
                if df['close'].iloc[j] > projected_high * 1.02:  # 2% Durchbruch nach oben
                    confirmed = True
                    breakout_idx = j
                    break
            
            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                target = None
                
                if confirmed:
                    # Kursziel: Projektion der Diamanthöhe nach oben
                    diamond_height = diamond_width * ((mid_high + mid_low) / 2)
                    target = df['close'].iloc[breakout_idx] + diamond_height
                
                patterns.append({
                    "type": "diamond_bottom",
                    "start_idx": i,
                    "mid_idx": mid_idx,
                    "end_idx": end_idx,
                    "width": diamond_width,
                    "first_high_slope": first_high_slope,
                    "first_high_intercept": first_high_intercept,
                    "first_low_slope": first_low_slope,
                    "first_low_intercept": first_low_intercept,
                    "second_high_slope": second_high_slope,
                    "second_high_intercept": second_high_intercept,
                    "second_low_slope": second_low_slope,
                    "second_low_intercept": second_low_intercept,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target,
                    "stop_loss": min(segment['low']) * 0.98  # 2% unter dem tiefsten Punkt
                })
    
    # Sortiere Muster nach Qualität
    if patterns:
        patterns.sort(key=lambda x: x["width"], reverse=True)
        return patterns[:3]  # Maximal 3 Ergebnisse
    
    return patterns


# ==============================================================================
#                      RENDER DIAMOND PATTERNS IN MATPLOTLIB
# ==============================================================================

def render_diamond_top(ax, df, pattern):
    """
    Zeichnet ein Diamond Top Pattern auf die Achse
    """
    # Extrahiere die Hauptpunkte des Patterns
    start_idx = pattern['start_idx']
    mid_idx = pattern['mid_idx']
    end_idx = pattern['end_idx']

    # Berechne Punkte für die erste Hälfte (Erweiterung)
    x1_range = range(start_idx, mid_idx + 1)
    upper1_y = [pattern['first_high_intercept'] + pattern['first_high_slope'] * (x - start_idx) for x in x1_range]
    lower1_y = [pattern['first_low_intercept'] + pattern['first_low_slope'] * (x - start_idx) for x in x1_range]

    # Berechne Punkte für die zweite Hälfte (Verengung)
    x2_range = range(mid_idx, end_idx + 1)
    upper2_y = [pattern['second_high_intercept'] + pattern['second_high_slope'] * (x - mid_idx) for x in x2_range]
    lower2_y = [pattern['second_low_intercept'] + pattern['second_low_slope'] * (x - mid_idx) for x in x2_range]

    # Zeichne die Diamond-Form
    ax.plot(x1_range, upper1_y, color='red', linewidth=2, alpha=0.7)
    ax.plot(x1_range, lower1_y, color='red', linewidth=2, alpha=0.7)
    ax.plot(x2_range, upper2_y, color='red', linewidth=2, alpha=0.7)
    ax.plot(x2_range, lower2_y, color='red', linewidth=2, alpha=0.7)

    # Bei bestätigten Patterns: Durchbruchspunkt und Kursziel zeichnen
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']
        ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                   color='red', s=80, marker='v')

        # Kursziel zeichnen
        if pattern.get('target') is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                       xmin=breakout_idx / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Diamanten)
        text_pos_x = mid_idx
        mid_high = pattern['first_high_intercept'] + pattern['first_high_slope'] * (mid_idx - start_idx)
        mid_low = pattern['first_low_intercept'] + pattern['first_low_slope'] * (mid_idx - start_idx)
        text_pos_y = (mid_high + mid_low) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_diamond_bottom(ax, df, pattern):
    """
    Zeichnet ein Diamond Bottom Pattern auf die Achse
    """
    # Extrahiere die Hauptpunkte des Patterns
    start_idx = pattern['start_idx']
    mid_idx = pattern['mid_idx']
    end_idx = pattern['end_idx']

    # Berechne Punkte für die erste Hälfte (Erweiterung)
    x1_range = range(start_idx, mid_idx + 1)
    upper1_y = [pattern['first_high_intercept'] + pattern['first_high_slope'] * (x - start_idx) for x in x1_range]
    lower1_y = [pattern['first_low_intercept'] + pattern['first_low_slope'] * (x - start_idx) for x in x1_range]

    # Berechne Punkte für die zweite Hälfte (Verengung)
    x2_range = range(mid_idx, end_idx + 1)
    upper2_y = [pattern['second_high_intercept'] + pattern['second_high_slope'] * (x - mid_idx) for x in x2_range]
    lower2_y = [pattern['second_low_intercept'] + pattern['second_low_slope'] * (x - mid_idx) for x in x2_range]

    # Zeichne die Diamond-Form
    ax.plot(x1_range, upper1_y, color='lime', linewidth=2, alpha=0.7)
    ax.plot(x1_range, lower1_y, color='lime', linewidth=2, alpha=0.7)
    ax.plot(x2_range, upper2_y, color='lime', linewidth=2, alpha=0.7)
    ax.plot(x2_range, lower2_y, color='lime', linewidth=2, alpha=0.7)

    # Bei bestätigten Patterns: Durchbruchspunkt und Kursziel zeichnen
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']
        ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                   color='lime', s=80, marker='^')

        # Kursziel zeichnen
        if pattern.get('target') is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color='lime', linestyle=':', alpha=0.5,
                       xmin=breakout_idx / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Diamanten)
        text_pos_x = pattern['mid_idx']
        mid_high = pattern['first_high_intercept'] + pattern['first_high_slope'] * (pattern['mid_idx'] - pattern['start_idx'])
        mid_low = pattern['first_low_intercept'] + pattern['first_low_slope'] * (pattern['mid_idx'] - pattern['start_idx'])
        text_pos_y = (mid_high + mid_low) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_pattern(ax, df, pattern):
    """
    Rendert ein Diamond-Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "diamond_top":
        render_diamond_top(ax, df, pattern)
    elif pattern_type == "diamond_bottom":
        render_diamond_bottom(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Diamond: {pattern_type}")

# ==============================================================================
#                      RENDER DIAMOND IN PLOTLY
# ==============================================================================

# Pattern-spezifische Plotly Renderer definieren...
def render_diamond_top_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass

# Pattern-spezifische Plotly Renderer definieren...
def render_diamond_bottom_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "diamond_top":
        render_diamond_top_plotly(fig, df, pattern)
    elif pattern_type == "diamond_bottom":
        render_diamond_bottom_plotly(fig, df, pattern)
    # ... weitere Pattern-Typen in dieser Datei ...
    else:
        print(f"Unbekannter Pattern-Typ für DATEI_NAME (Plotly): {pattern_type}")
