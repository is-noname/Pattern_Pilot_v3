#import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT RECTANGLES
# ==============================================================================
def detect_bullish_rectangle(df, config=None, timeframe="1d"):
    """
    Erkennt bullische Rechtecke (Fortsetzungsmuster im Aufwärtstrend)
    
    Eigenschaften:
    - Horizontale Unterstützungs- und Widerstandslinien
    - Seitwärtsbewegung zwischen diesen Linien
    - Ausbruch nach oben signalisiert Fortsetzung des Aufwärtstrends
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("bullish_rectangle", PATTERN_CONFIGS.get("bullish_rectangle", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 50)
    min_touches = config.get("min_touches", 2)  # Mindestanzahl Berührungen pro Linie
    max_slope = config.get("max_slope", 0.02)  # Maximale Steigung für "horizontale" Linien
    min_width = config.get("min_width", 0.03)  # Mindestbreite als Prozentsatz des Preises

    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Suche nach potenziellen Rechteckformationen
    step_size = max(1, min(10, len(df) // 20))  # Optimierung: nicht jeden möglichen Startpunkt prüfen
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length

            if end_idx >= len(df):
                continue

            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            
            # Finde die lokalen Hochs und Tiefs im Segment
            highs = []
            lows = []
            
            # Vereinfachter Ansatz: Teile das Segment in mehrere Teile und finde Extremwerte
            num_parts = max(4, pattern_length // 5)  # Mindestens 4 Teile oder mehr für längere Muster
            part_length = len(segment) // num_parts
            
            if part_length == 0:
                continue
            
            for j in range(num_parts):
                start_part = j * part_length
                end_part = min((j + 1) * part_length, len(segment))
                
                if end_part <= start_part:
                    continue
                    
                part = segment.iloc[start_part:end_part]
                
                # Finde lokales Hoch und Tief in diesem Teil
                high_idx = part['high'].idxmax()
                low_idx = part['low'].idxmin()
                
                highs.append((high_idx, df.loc[high_idx, 'high']))
                lows.append((low_idx, df.loc[low_idx, 'low']))
            
            # Prüfe, ob genügend Punkte vorhanden sind
            if len(highs) < min_touches or len(lows) < min_touches:
                continue
                
            # Berechne die Trendlinien für Hochs und Tiefs
            high_x = np.array([df.index.get_loc(p[0]) for p in highs])
            high_y = np.array([p[1] for p in highs])
            
            low_x = np.array([df.index.get_loc(p[0]) for p in lows])
            low_y = np.array([p[1] for p in lows])
            
            try:
                # Lineare Regression für Hochs (Widerstandslinie)
                upper_slope, upper_intercept = np.polyfit(high_x, high_y, 1)
                
                # Lineare Regression für Tiefs (Unterstützungslinie)
                lower_slope, lower_intercept = np.polyfit(low_x, low_y, 1)
            except:
                continue  # Falls Regression fehlschlägt
                
            # Für ein Rechteck sollten beide Linien nahezu horizontal sein
            if abs(upper_slope) > max_slope or abs(lower_slope) > max_slope:
                continue
                
            # Berechne die durchschnittlichen Höhen für Widerstand und Unterstützung
            resistance_level = np.mean(high_y)
            support_level = np.mean(low_y)
            
            # Prüfe die Mindestbreite des Rechtecks
            rectangle_height = resistance_level - support_level
            avg_price = (resistance_level + support_level) / 2
            
            if rectangle_height / avg_price < min_width:
                continue
                
            # Prüfe, ob ein Aufwärtstrend vor dem Rechteck besteht
            # (Für bullisches Rechteck sollte es ein vorheriger Aufwärtstrend sein)
            trend_start = max(0, i - min_pattern_bars)
            pre_pattern = df.iloc[trend_start:i]
            
            if len(pre_pattern) > 5:  # Genug Daten für Trendanalyse
                pre_trend_slope = np.polyfit(range(len(pre_pattern)), pre_pattern['close'].values, 1)[0]
                if pre_trend_slope <= 0:  # Kein Aufwärtstrend vor dem Rechteck
                    continue
            
            # Suche nach Ausbruch über die Widerstandslinie
            confirmed = False
            breakout_idx = None
            
            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                if df['close'].iloc[j] > resistance_level * 1.01:  # 1% Ausbruch
                    confirmed = True
                    breakout_idx = j
                    break
                    
            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                target = None
                
                if confirmed:
                    # Kursziel: Höhe des Rechtecks vom Ausbruchspunkt nach oben projiziert
                    target = df['close'].iloc[breakout_idx] + rectangle_height
                    
                patterns.append({
                    "type": "bullish_rectangle",
                    "start_idx": i,
                    "end_idx": end_idx,
                    "resistance_level": resistance_level,
                    "support_level": support_level,
                    "height": rectangle_height,
                    "upper_slope": upper_slope,
                    "upper_intercept": upper_intercept,
                    "lower_slope": lower_slope,
                    "lower_intercept": lower_intercept,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target,
                    "high_points": highs,
                    "low_points": lows,
                    "stop_loss": support_level * 0.98  # 2% unter der Unterstützungslinie
                })
                
    # Sortiere nach Qualität und begrenze Anzahl
    if patterns:
        # Sortiere nach Höhe und Länge des Musters
        patterns.sort(key=lambda x: (x["height"] * (x["end_idx"] - x["start_idx"])), reverse=True)
        return patterns[:3]  # Maximal 3 Ergebnisse zurückgeben
                
    return patterns


def detect_bearish_rectangle(df, config=None, timeframe="1d"):
    """
    Erkennt bearische Rechtecke (Fortsetzungsmuster im Abwärtstrend)
    
    Eigenschaften:
    - Horizontale Unterstützungs- und Widerstandslinien
    - Seitwärtsbewegung zwischen diesen Linien
    - Ausbruch nach unten signalisiert Fortsetzung des Abwärtstrends
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("bearish_rectangle", PATTERN_CONFIGS.get("bearish_rectangle", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 50)
    min_touches = config.get("min_touches", 2)  # Mindestanzahl Berührungen pro Linie
    max_slope = config.get("max_slope", 0.02)  # Maximale Steigung für "horizontale" Linien
    min_width = config.get("min_width", 0.03)  # Mindestbreite als Prozentsatz des Preises

    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Suche nach potenziellen Rechteckformationen
    step_size = max(1, min(10, len(df) // 20))  # Optimierung: nicht jeden möglichen Startpunkt prüfen
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length

            if end_idx >= len(df):
                continue

            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            
            # Finde die lokalen Hochs und Tiefs im Segment
            highs = []
            lows = []
            
            # Vereinfachter Ansatz: Teile das Segment in mehrere Teile und finde Extremwerte
            num_parts = max(4, pattern_length // 5)  # Mindestens 4 Teile oder mehr für längere Muster
            part_length = len(segment) // num_parts
            
            if part_length == 0:
                continue
            
            for j in range(num_parts):
                start_part = j * part_length
                end_part = min((j + 1) * part_length, len(segment))
                
                if end_part <= start_part:
                    continue
                    
                part = segment.iloc[start_part:end_part]
                
                # Finde lokales Hoch und Tief in diesem Teil
                high_idx = part['high'].idxmax()
                low_idx = part['low'].idxmin()
                
                highs.append((high_idx, df.loc[high_idx, 'high']))
                lows.append((low_idx, df.loc[low_idx, 'low']))
            
            # Prüfe, ob genügend Punkte vorhanden sind
            if len(highs) < min_touches or len(lows) < min_touches:
                continue
                
            # Berechne die Trendlinien für Hochs und Tiefs
            high_x = np.array([df.index.get_loc(p[0]) for p in highs])
            high_y = np.array([p[1] for p in highs])
            
            low_x = np.array([df.index.get_loc(p[0]) for p in lows])
            low_y = np.array([p[1] for p in lows])
            
            try:
                # Lineare Regression für Hochs (Widerstandslinie)
                upper_slope, upper_intercept = np.polyfit(high_x, high_y, 1)
                
                # Lineare Regression für Tiefs (Unterstützungslinie)
                lower_slope, lower_intercept = np.polyfit(low_x, low_y, 1)
            except:
                continue  # Falls Regression fehlschlägt
                
            # Für ein Rechteck sollten beide Linien nahezu horizontal sein
            if abs(upper_slope) > max_slope or abs(lower_slope) > max_slope:
                continue
                
            # Berechne die durchschnittlichen Höhen für Widerstand und Unterstützung
            resistance_level = np.mean(high_y)
            support_level = np.mean(low_y)
            
            # Prüfe die Mindestbreite des Rechtecks
            rectangle_height = resistance_level - support_level
            avg_price = (resistance_level + support_level) / 2
            
            if rectangle_height / avg_price < min_width:
                continue
                
            # Prüfe, ob ein Abwärtstrend vor dem Rechteck besteht
            # (Für bearisches Rechteck sollte es ein vorheriger Abwärtstrend sein)
            trend_start = max(0, i - min_pattern_bars)
            pre_pattern = df.iloc[trend_start:i]
            
            if len(pre_pattern) > 5:  # Genug Daten für Trendanalyse
                pre_trend_slope = np.polyfit(range(len(pre_pattern)), pre_pattern['close'].values, 1)[0]
                if pre_trend_slope >= 0:  # Kein Abwärtstrend vor dem Rechteck
                    continue
            
            # Suche nach Ausbruch unter die Unterstützungslinie
            confirmed = False
            breakout_idx = None
            
            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                if df['close'].iloc[j] < support_level * 0.99:  # 1% Ausbruch nach unten
                    confirmed = True
                    breakout_idx = j
                    break
                    
            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                target = None
                
                if confirmed:
                    # Kursziel: Höhe des Rechtecks vom Ausbruchspunkt nach unten projiziert
                    target = df['close'].iloc[breakout_idx] - rectangle_height
                    
                patterns.append({
                    "type": "bearish_rectangle",
                    "start_idx": i,
                    "end_idx": end_idx,
                    "resistance_level": resistance_level,
                    "support_level": support_level,
                    "height": rectangle_height,
                    "upper_slope": upper_slope,
                    "upper_intercept": upper_intercept,
                    "lower_slope": lower_slope,
                    "lower_intercept": lower_intercept,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target,
                    "high_points": highs,
                    "low_points": lows,
                    "stop_loss": resistance_level * 1.02  # 2% über der Widerstandslinie
                })
                
    # Sortiere nach Qualität und begrenze Anzahl
    if patterns:
        # Sortiere nach Höhe und Länge des Musters
        patterns.sort(key=lambda x: (x["height"] * (x["end_idx"] - x["start_idx"])), reverse=True)
        return patterns[:3]  # Maximal 3 Ergebnisse zurückgeben
                
    return patterns


# ==============================================================================
#                      RENDER RECTANGLES IN MATPLOTLIB
# ==============================================================================
def render_bullish_rectangle(ax, df, pattern):
    """
    Zeichnet ein bullisches Rechteck auf die Achse
    """
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # Zeichne horizontale Widerstandslinie
    ax.axhline(y=pattern['resistance_level'], color='r', linestyle='--', alpha=0.7,
               xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Zeichne horizontale Unterstützungslinie
    ax.axhline(y=pattern['support_level'], color='g', linestyle='--', alpha=0.7,
               xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Zeichne Berührungspunkte
    if 'high_points' in pattern:
        for point in pattern['high_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    if 'low_points' in pattern:
        for point in pattern['low_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    # Zeichne Ausbruchspunkt, wenn bestätigt
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                   color='lime', s=80, marker='^')

        # Kursziel anzeigen
        if pattern['target'] is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color='lime', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Rechtecks)
        text_pos_x = (start_idx + end_idx) // 2
        text_pos_y = (pattern['resistance_level'] + pattern['support_level']) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_bearish_rectangle(ax, df, pattern):
    """
    Zeichnet ein bearisches Rechteck auf die Achse
    """
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # Zeichne horizontale Widerstandslinie
    ax.axhline(y=pattern['resistance_level'], color='r', linestyle='--', alpha=0.7,
               xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Zeichne horizontale Unterstützungslinie
    ax.axhline(y=pattern['support_level'], color='g', linestyle='--', alpha=0.7,
               xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Zeichne Berührungspunkte
    if 'high_points' in pattern:
        for point in pattern['high_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    if 'low_points' in pattern:
        for point in pattern['low_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    # Zeichne Ausbruchspunkt, wenn bestätigt
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                   color='red', s=80, marker='v')

        # Kursziel anzeigen
        if pattern['target'] is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Rechtecks)
        text_pos_x = (start_idx + end_idx) // 2
        text_pos_y = (pattern['resistance_level'] + pattern['support_level']) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_pattern(ax, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "bullish_rectangle":
        render_bullish_rectangle(ax, df, pattern)
    elif pattern_type == "bearish_rectangle":
        render_bearish_rectangle(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Rectangles: {pattern_type}")

# ==============================================================================
#                      RENDER RECTANGLES IN PLOTLY
# ==============================================================================

# Pattern-spezifische Plotly Renderer definieren...
def render_bullish_rectangle_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass

# Pattern-spezifische Plotly Renderer definieren...
def render_bearish_rectangle_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", 'unknown')

    if pattern_type == "bullish_rectangle":
        render_bullish_rectangle_plotly(fig, df, pattern)
    elif pattern_type == "bearish_rectangle":
        render_bearish_rectangle_plotly(fig, df, pattern)
    # ... weitere Pattern-Typen in dieser Datei ...
    else:
        print(f"Unbekannter Pattern-Typ für DATEI_NAME (Plotly): {pattern_type}")