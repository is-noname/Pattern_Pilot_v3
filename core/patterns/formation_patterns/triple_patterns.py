#import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS
import plotly.graph_objects as go

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen

# ==============================================================================
#                      DETECT TRIPLE PATTERNS
# ==============================================================================
def detect_triple_top(df, config=None, timeframe="1d"):
    """
    Erkennt Triple-Top-Muster (bearishes Umkehrmuster)
    
    Eigenschaften:
    - Drei aufeinanderfolgende Hochs auf etwa gleichem Niveau
    - Muss nach einem Aufwärtstrend auftreten
    - Nackenlinie wird durch die Tiefs zwischen den Hochs gebildet
    - Durchbruch unter die Nackenlinie bestätigt das Muster
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("triple_top", PATTERN_CONFIGS.get("triple_top", {}), timeframe)

    tolerance = config.get("tolerance", 0.03)
    lookback_periods = config.get("lookback_periods", 5)
    min_pattern_bars = config.get("min_pattern_bars", 5)

    if len(df) < lookback_periods * 2 + min_pattern_bars * 2:
        return []  # Nicht genug Daten

    highs = df['high'].values
    tops = []

    # Finde lokale Hochs
    for i in range(lookback_periods, len(highs) - lookback_periods):
        prev = np.max(highs[i - lookback_periods:i])
        next_ = np.max(highs[i + 1:i + lookback_periods + 1])
        if highs[i] > prev and highs[i] > next_:
            tops.append(i)

    patterns = []
    # Brauchen mindestens 3 Tops für Triple Top
    if len(tops) < 3:
        return patterns

    # Suche nach Triple-Top-Formationen
    for i in range(len(tops) - 2):
        first_top_idx = tops[i]
        second_top_idx = tops[i + 1]
        third_top_idx = tops[i + 2]

        # Prüfe Abstand zwischen den Hochs
        if (third_top_idx - first_top_idx) < 2 * min_pattern_bars:
            continue

        # Prüfe, ob alle drei Hochs auf etwa gleichem Niveau liegen
        top1 = highs[first_top_idx]
        top2 = highs[second_top_idx]
        top3 = highs[third_top_idx]
        
        avg_top = (top1 + top2 + top3) / 3.0
        
        if (abs(top1 - avg_top) / avg_top > tolerance or
            abs(top2 - avg_top) / avg_top > tolerance or
            abs(top3 - avg_top) / avg_top > tolerance):
            continue
        
        # Finde die Tiefs zwischen den Hochs
        first_trough_range = range(first_top_idx + 1, second_top_idx)
        second_trough_range = range(second_top_idx + 1, third_top_idx)
        
        if not first_trough_range or not second_trough_range:
            continue
        
        first_trough_idx = first_top_idx + 1 + np.argmin(df['low'].values[first_trough_range])
        second_trough_idx = second_top_idx + 1 + np.argmin(df['low'].values[second_trough_range])
        
        first_trough = df['low'].values[first_trough_idx]
        second_trough = df['low'].values[second_trough_idx]
        
        # Bestimme Nackenlinie (kann leicht geneigt sein)
        neckline_level = min(first_trough, second_trough)
        
        # Prüfe auf Durchbruch unter die Nackenlinie
        confirmed = False
        breakout_idx = None
        
        for j in range(third_top_idx + 1, min(len(df), third_top_idx + 30)):
            if df['close'].values[j] < neckline_level:
                confirmed = True
                breakout_idx = j
                break
                
        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Nackenlinie - Höhe des Musters
                pattern_height = avg_top - neckline_level
                target = neckline_level - pattern_height
                
            patterns.append({
                "type": "triple_top",
                "first_top": first_top_idx,
                "second_top": second_top_idx,
                "third_top": third_top_idx,
                "first_trough": first_trough_idx,
                "second_trough": second_trough_idx,
                "neckline": neckline_level,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": max(top1, top2, top3) * 1.02  # 2% über dem höchsten Top
            })
            
    return patterns


def detect_triple_bottom(df, config=None, timeframe="1d"):
    """
    Erkennt Triple-Bottom-Muster (bullishes Umkehrmuster)
    
    Eigenschaften:
    - Drei aufeinanderfolgende Tiefs auf etwa gleichem Niveau
    - Muss nach einem Abwärtstrend auftreten
    - Nackenlinie wird durch die Hochs zwischen den Tiefs gebildet
    - Durchbruch über die Nackenlinie bestätigt das Muster
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("triple_bottom", PATTERN_CONFIGS.get("triple_bottom", {}), timeframe)

    tolerance = config.get("tolerance", 0.03)
    lookback_periods = config.get("lookback_periods", 5)
    min_pattern_bars = config.get("min_pattern_bars", 5)

    if len(df) < lookback_periods * 2 + min_pattern_bars * 2:
        return []  # Nicht genug Daten

    lows = df['low'].values
    bottoms = []

    # Finde lokale Tiefs
    for i in range(lookback_periods, len(lows) - lookback_periods):
        prev = np.min(lows[i - lookback_periods:i])
        next_ = np.min(lows[i + 1:i + lookback_periods + 1])
        if lows[i] < prev and lows[i] < next_:
            bottoms.append(i)

    patterns = []
    # Brauchen mindestens 3 Bottoms für Triple Bottom
    if len(bottoms) < 3:
        return patterns

    # Suche nach Triple-Bottom-Formationen
    for i in range(len(bottoms) - 2):
        first_bottom_idx = bottoms[i]
        second_bottom_idx = bottoms[i + 1]
        third_bottom_idx = bottoms[i + 2]

        # Prüfe Abstand zwischen den Tiefs
        if (third_bottom_idx - first_bottom_idx) < 2 * min_pattern_bars:
            continue

        # Prüfe, ob alle drei Tiefs auf etwa gleichem Niveau liegen
        bottom1 = lows[first_bottom_idx]
        bottom2 = lows[second_bottom_idx]
        bottom3 = lows[third_bottom_idx]
        
        avg_bottom = (bottom1 + bottom2 + bottom3) / 3.0
        
        if (abs(bottom1 - avg_bottom) / avg_bottom > tolerance or
            abs(bottom2 - avg_bottom) / avg_bottom > tolerance or
            abs(bottom3 - avg_bottom) / avg_bottom > tolerance):
            continue
        
        # Finde die Hochs zwischen den Tiefs
        first_peak_range = range(first_bottom_idx + 1, second_bottom_idx)
        second_peak_range = range(second_bottom_idx + 1, third_bottom_idx)
        
        if not first_peak_range or not second_peak_range:
            continue
        
        first_peak_idx = first_bottom_idx + 1 + np.argmax(df['high'].values[first_peak_range])
        second_peak_idx = second_bottom_idx + 1 + np.argmax(df['high'].values[second_peak_range])
        
        first_peak = df['high'].values[first_peak_idx]
        second_peak = df['high'].values[second_peak_idx]
        
        # Bestimme Nackenlinie (kann leicht geneigt sein)
        neckline_level = max(first_peak, second_peak)
        
        # Prüfe auf Durchbruch über die Nackenlinie
        confirmed = False
        breakout_idx = None
        
        for j in range(third_bottom_idx + 1, min(len(df), third_bottom_idx + 30)):
            if df['close'].values[j] > neckline_level:
                confirmed = True
                breakout_idx = j
                break
                
        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Nackenlinie + Höhe des Musters
                pattern_height = neckline_level - avg_bottom
                target = neckline_level + pattern_height
                
            patterns.append({
                "type": "triple_bottom",
                "first_bottom": first_bottom_idx,
                "second_bottom": second_bottom_idx,
                "third_bottom": third_bottom_idx,
                "first_peak": first_peak_idx,
                "second_peak": second_peak_idx,
                "neckline": neckline_level,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": min(bottom1, bottom2, bottom3) * 0.98  # 2% unter dem tiefsten Bottom
            })
            
    return patterns

# ==============================================================================
#                      RENDER TRIPLE PATTERNS MATPLOTLIB
# ==============================================================================
def render_triple_top(ax, df, pattern):
    """
    Zeichnet ein Triple Top Muster auf die Achse
    """
    # Die drei Hochpunkte markieren
    ax.scatter(pattern['first_top'], df['high'].iloc[pattern['first_top']],
               color='red', s=100, marker='o')
    ax.scatter(pattern['second_top'], df['high'].iloc[pattern['second_top']],
               color='red', s=100, marker='o')
    ax.scatter(pattern['third_top'], df['high'].iloc[pattern['third_top']],
               color='red', s=100, marker='o')

    # Nackenlinie zeichnen
    ax.axhline(y=pattern['neckline'], color='r', linestyle='--', alpha=0.7,
               xmin=pattern['first_top'] / len(df), xmax=pattern['third_top'] / len(df))

    # Durchbruch (wenn bestätigt)
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                   color='white', s=80, marker='v')

        # Kursziel anzeigen
        if pattern['target'] is not None:
            # Gepunktete Linie zum Kursziel
            target_y = pattern['target']
            ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (über dem zweiten Top)
        text_pos_x = pattern['second_top']
        text_pos_y = df['high'].iloc[pattern['second_top']] * 1.02

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_triple_bottom(ax, df, pattern):
    """
    Zeichnet ein Triple Bottom Muster auf die Achse
    """
    # Die drei Tiefpunkte markieren
    ax.scatter(pattern['first_bottom'], df['low'].iloc[pattern['first_bottom']],
               color='lime', s=100, marker='o')
    ax.scatter(pattern['second_bottom'], df['low'].iloc[pattern['second_bottom']],
               color='lime', s=100, marker='o')
    ax.scatter(pattern['third_bottom'], df['low'].iloc[pattern['third_bottom']],
               color='lime', s=100, marker='o')

    # Nackenlinie zeichnen
    ax.axhline(y=pattern['neckline'], color='g', linestyle='--', alpha=0.7,
               xmin=pattern['first_bottom'] / len(df), xmax=pattern['third_bottom'] / len(df))

    # Durchbruch (wenn bestätigt)
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                   color='lime', s=80, marker='^')

        # Kursziel anzeigen
        if pattern['target'] is not None:
            # Gepunktete Linie zum Kursziel
            target_y = pattern['target']
            ax.axhline(y=target_y, color='lime', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (unter dem zweiten Bottom)
        text_pos_x = pattern['second_bottom']
        text_pos_y = df['low'].iloc[pattern['second_bottom']] * 0.98

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_pattern(ax, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "triple_top":
        render_triple_top(ax, df, pattern)
    elif pattern_type == "triple_bottom":
        render_triple_bottom(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Triple-Patterns: {pattern_type}")

# ==============================================================================
#                      RENDER TRIPLE PATTERNS PLOTLY
# ==============================================================================
def render_triple_bottom_plotly(fig, df, pattern):
    """Plotly Version des Triple Bottom Pattern Renderers"""
    # ... [Code hier] ...
    pass

def render_triple_top_plotly(fig, df, pattern):
    """Plotly Version des Triple Top Pattern Renderers"""
    # ... [Code hier] ...
    pass

def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "triple_top":
        render_triple_top_plotly(fig, df, pattern)
    elif pattern_type == "triple_bottom":
        render_triple_bottom_plotly(fig, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Triple-Patterns (Plotly): {pattern_type}")