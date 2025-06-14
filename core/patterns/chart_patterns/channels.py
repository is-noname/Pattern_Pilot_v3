import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen



def detect_upward_channel(df, config=None, timeframe="1d"):
    """
    Erkennt aufwärtsgerichtete Kanäle (Trendfortsetzungsmuster in Aufwärtstrends)
    
    Eigenschaften:
    - Zwei parallele, aufwärtsgerichtete Trendlinien
    - Obere Linie verbindet Hochs, untere Linie verbindet Tiefs
    - Preis bewegt sich konsistent innerhalb des Kanals
    - Ausbruch aus dem Kanal kann Trendwechsel signalisieren
    """
    # Config laden
    if config is None:
        config = PATTERN_CONFIGS.get("upward_channel", {})

    min_pattern_bars = config.get("min_pattern_bars", 15)
    max_pattern_bars = config.get("max_pattern_bars", 120)
    min_touches = config.get("min_touches", 3)  # Mindestberührungen pro Kanal-Linie
    min_slope = config.get("min_slope", 0.0005)  # Minimale Steigung für aufwärts gerichtete Linien
    max_slope_diff = config.get("max_slope_diff", 0.2)  # Max. Unterschied zwischen Linien-Steigungen (Parallelität)
    min_width = config.get("min_width", 0.03)  # Mindestbreite des Kanals als % des Preises
    
    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten
        
    patterns = []
    
    # Nicht jeden möglichen Startpunkt prüfen, sondern in Schritten
    step_size = max(1, min(20, len(df) // 20))
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length
            
            if end_idx >= len(df):
                continue
                
            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            
            # Finde potenzielle Berührungspunkte für obere und untere Kanallinie
            
            # Für einen präziseren Kanal identifizieren wir lokale Extrema
            # und verwenden nur diese für die Regression
            
            # 1. Teile das Segment in mehrere Teile
            num_parts = max(5, pattern_length // 10)  # Mindestens 5 Teile
            part_length = len(segment) // num_parts
            
            if part_length == 0:
                continue
                
            upper_points = []  # Für obere Kanallinie (Hochs)
            lower_points = []  # Für untere Kanallinie (Tiefs)
            
            # Finde lokale Extrema in jedem Teil
            for j in range(num_parts):
                start_part = j * part_length
                end_part = min((j + 1) * part_length, len(segment))
                
                if end_part <= start_part + 2:  # Brauchen mindestens 3 Punkte
                    continue
                    
                part = segment.iloc[start_part:end_part]
                
                # Lokale Hochs und Tiefs finden (mit einfacher Methode)
                for k in range(1, len(part) - 1):
                    # Lokales Hoch
                    if part['high'].iloc[k] > part['high'].iloc[k-1] and part['high'].iloc[k] > part['high'].iloc[k+1]:
                        idx = part.index[k]
                        upper_points.append((df.index.get_loc(idx), part['high'].iloc[k]))
                    
                    # Lokales Tief
                    if part['low'].iloc[k] < part['low'].iloc[k-1] and part['low'].iloc[k] < part['low'].iloc[k+1]:
                        idx = part.index[k]
                        lower_points.append((df.index.get_loc(idx), part['low'].iloc[k]))
            
            # Wenn nicht genug Punkte gefunden wurden, füge die absoluten Extrema hinzu
            if len(upper_points) < min_touches:
                high_idx = segment['high'].idxmax()
                upper_points.append((df.index.get_loc(high_idx), segment['high'].max()))
                
            if len(lower_points) < min_touches:
                low_idx = segment['low'].idxmin()
                lower_points.append((df.index.get_loc(low_idx), segment['low'].min()))
                
            # Immer noch nicht genug Punkte?
            if len(upper_points) < min_touches or len(lower_points) < min_touches:
                continue
                
            # Sortiere nach x-Wert (Index)
            upper_points.sort(key=lambda x: x[0])
            lower_points.sort(key=lambda x: x[0])
            
            # Linear Regression für obere Linie
            upper_x = [p[0] for p in upper_points]
            upper_y = [p[1] for p in upper_points]
            
            # Linear Regression für untere Linie
            lower_x = [p[0] for p in lower_points]
            lower_y = [p[1] for p in lower_points]
            
            try:
                # Obere Trendlinie
                upper_slope, upper_intercept = np.polyfit(upper_x, upper_y, 1)
                
                # Untere Trendlinie
                lower_slope, lower_intercept = np.polyfit(lower_x, lower_y, 1)
            except:
                continue  # Falls Regression fehlschlägt
                
            # Für aufwärts gerichtete Kanäle: beide Linien müssen aufwärts gerichtet sein
            if upper_slope < min_slope or lower_slope < min_slope:
                continue
                
            # Die Linien sollten etwa parallel sein (ähnliche Steigung)
            slope_diff_ratio = abs(upper_slope - lower_slope) / max(upper_slope, lower_slope)
            if slope_diff_ratio > max_slope_diff:
                continue
                
            # Prüfe Kanalbreite
            # Berechne mittlere Preise im Segment
            mid_idx = i + pattern_length // 2
            mid_idx_loc = df.index.get_loc(df.index[mid_idx])
            
            upper_mid = upper_intercept + upper_slope * mid_idx_loc
            lower_mid = lower_intercept + lower_slope * mid_idx_loc
            
            channel_width = upper_mid - lower_mid
            avg_price = df['close'].iloc[mid_idx]
            
            if channel_width / avg_price < min_width:
                continue
                
            # Suche nach Ausbruch aus dem Kanal (kann nach oben oder unten erfolgen)
            breakout_up = False
            breakout_down = False
            breakout_idx = None
            
            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                j_loc = df.index.get_loc(df.index[j])
                
                # Projizierte Kanal-Linien
                projected_upper = upper_intercept + upper_slope * j_loc
                projected_lower = lower_intercept + lower_slope * j_loc
                
                # Ausbruch nach oben
                if df['close'].iloc[j] > projected_upper * 1.01:  # 1% Ausbruch
                    breakout_up = True
                    breakout_idx = j
                    break
                    
                # Ausbruch nach unten
                if df['close'].iloc[j] < projected_lower * 0.99:  # 1% Ausbruch
                    breakout_down = True
                    breakout_idx = j
                    break
            
            # Muster hinzufügen
            patterns.append({
                "type": "upward_channel",
                "start_idx": i,
                "end_idx": end_idx,
                "upper_slope": upper_slope,
                "upper_intercept": upper_intercept,
                "lower_slope": lower_slope,
                "lower_intercept": lower_intercept,
                "width": channel_width,
                "upper_points": upper_points,
                "lower_points": lower_points,
                "breakout_up": breakout_up,
                "breakout_down": breakout_down,
                "breakout_idx": breakout_idx,
                "target": None  # Kein spezifisches Kursziel für Kanäle, da sie Trendfortsetzung repräsentieren
            })
            
    # Sortiere nach Qualität und begrenze Anzahl
    if patterns:
        # Sortiere nach Länge und Breite des Kanals
        patterns.sort(key=lambda x: (x["end_idx"] - x["start_idx"]) * x["width"], reverse=True)
        return patterns[:3]  # Max. 3 Ergebnisse
        
    return patterns


def detect_downward_channel(df, config=None, timeframe="1d"):
    """
    Erkennt abwärtsgerichtete Kanäle (Trendfortsetzungsmuster in Abwärtstrends)
    
    Eigenschaften:
    - Zwei parallele, abwärtsgerichtete Trendlinien
    - Obere Linie verbindet Hochs, untere Linie verbindet Tiefs
    - Preis bewegt sich konsistent innerhalb des Kanals
    - Ausbruch aus dem Kanal kann Trendwechsel signalisieren
    """
    # Config laden
    if config is None:
        config = PATTERN_CONFIGS.get("downward_channel", {})

    min_pattern_bars = config.get("min_pattern_bars", 15)
    max_pattern_bars = config.get("max_pattern_bars", 120)
    min_touches = config.get("min_touches", 3)  # Mindestberührungen pro Kanal-Linie
    min_slope = config.get("min_slope", 0.0005)  # Minimale Steigung für abwärts gerichtete Linien (positiver Wert!)
    max_slope_diff = config.get("max_slope_diff", 0.2)  # Max. Unterschied zwischen Linien-Steigungen (Parallelität)
    min_width = config.get("min_width", 0.03)  # Mindestbreite des Kanals als % des Preises
    
    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten
        
    patterns = []
    
    # Nicht jeden möglichen Startpunkt prüfen, sondern in Schritten
    step_size = max(1, min(20, len(df) // 20))
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length
            
            if end_idx >= len(df):
                continue
                
            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            
            # Finde potenzielle Berührungspunkte für obere und untere Kanallinie
            
            # Für einen präziseren Kanal identifizieren wir lokale Extrema
            # und verwenden nur diese für die Regression
            
            # 1. Teile das Segment in mehrere Teile
            num_parts = max(5, pattern_length // 10)  # Mindestens 5 Teile
            part_length = len(segment) // num_parts
            
            if part_length == 0:
                continue
                
            upper_points = []  # Für obere Kanallinie (Hochs)
            lower_points = []  # Für untere Kanallinie (Tiefs)
            
            # Finde lokale Extrema in jedem Teil
            for j in range(num_parts):
                start_part = j * part_length
                end_part = min((j + 1) * part_length, len(segment))
                
                if end_part <= start_part + 2:  # Brauchen mindestens 3 Punkte
                    continue
                    
                part = segment.iloc[start_part:end_part]
                
                # Lokale Hochs und Tiefs finden (mit einfacher Methode)
                for k in range(1, len(part) - 1):
                    # Lokales Hoch
                    if part['high'].iloc[k] > part['high'].iloc[k-1] and part['high'].iloc[k] > part['high'].iloc[k+1]:
                        idx = part.index[k]
                        upper_points.append((df.index.get_loc(idx), part['high'].iloc[k]))
                    
                    # Lokales Tief
                    if part['low'].iloc[k] < part['low'].iloc[k-1] and part['low'].iloc[k] < part['low'].iloc[k+1]:
                        idx = part.index[k]
                        lower_points.append((df.index.get_loc(idx), part['low'].iloc[k]))
            
            # Wenn nicht genug Punkte gefunden wurden, füge die absoluten Extrema hinzu
            if len(upper_points) < min_touches:
                high_idx = segment['high'].idxmax()
                upper_points.append((df.index.get_loc(high_idx), segment['high'].max()))
                
            if len(lower_points) < min_touches:
                low_idx = segment['low'].idxmin()
                lower_points.append((df.index.get_loc(low_idx), segment['low'].min()))
                
            # Immer noch nicht genug Punkte?
            if len(upper_points) < min_touches or len(lower_points) < min_touches:
                continue
                
            # Sortiere nach x-Wert (Index)
            upper_points.sort(key=lambda x: x[0])
            lower_points.sort(key=lambda x: x[0])
            
            # Linear Regression für obere Linie
            upper_x = [p[0] for p in upper_points]
            upper_y = [p[1] for p in upper_points]
            
            # Linear Regression für untere Linie
            lower_x = [p[0] for p in lower_points]
            lower_y = [p[1] for p in lower_points]
            
            try:
                # Obere Trendlinie
                upper_slope, upper_intercept = np.polyfit(upper_x, upper_y, 1)
                
                # Untere Trendlinie
                lower_slope, lower_intercept = np.polyfit(lower_x, lower_y, 1)
            except:
                continue  # Falls Regression fehlschlägt
                
            # Für abwärts gerichtete Kanäle: beide Linien müssen abwärts gerichtet sein
            if upper_slope > -min_slope or lower_slope > -min_slope:
                continue
                
            # Die Linien sollten etwa parallel sein (ähnliche Steigung)
            slope_diff_ratio = abs(upper_slope - lower_slope) / max(abs(upper_slope), abs(lower_slope))
            if slope_diff_ratio > max_slope_diff:
                continue
                
            # Prüfe Kanalbreite
            # Berechne mittlere Preise im Segment
            mid_idx = i + pattern_length // 2
            mid_idx_loc = df.index.get_loc(df.index[mid_idx])
            
            upper_mid = upper_intercept + upper_slope * mid_idx_loc
            lower_mid = lower_intercept + lower_slope * mid_idx_loc
            
            channel_width = upper_mid - lower_mid
            avg_price = df['close'].iloc[mid_idx]
            
            if channel_width / avg_price < min_width:
                continue
                
            # Suche nach Ausbruch aus dem Kanal (kann nach oben oder unten erfolgen)
            breakout_up = False
            breakout_down = False
            breakout_idx = None
            
            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                j_loc = df.index.get_loc(df.index[j])
                
                # Projizierte Kanal-Linien
                projected_upper = upper_intercept + upper_slope * j_loc
                projected_lower = lower_intercept + lower_slope * j_loc
                
                # Ausbruch nach oben
                if df['close'].iloc[j] > projected_upper * 1.01:  # 1% Ausbruch
                    breakout_up = True
                    breakout_idx = j
                    break
                    
                # Ausbruch nach unten
                if df['close'].iloc[j] < projected_lower * 0.99:  # 1% Ausbruch
                    breakout_down = True
                    breakout_idx = j
                    break
            
            # Muster hinzufügen
            patterns.append({
                "type": "downward_channel",
                "start_idx": i,
                "end_idx": end_idx,
                "upper_slope": upper_slope,
                "upper_intercept": upper_intercept,
                "lower_slope": lower_slope,
                "lower_intercept": lower_intercept,
                "width": channel_width,
                "upper_points": upper_points,
                "lower_points": lower_points,
                "breakout_up": breakout_up,
                "breakout_down": breakout_down,
                "breakout_idx": breakout_idx,
                "target": None  # Kein spezifisches Kursziel für Kanäle, da sie Trendfortsetzung repräsentieren
            })
            
    # Sortiere nach Qualität und begrenze Anzahl
    if patterns:
        # Sortiere nach Länge und Breite des Kanals
        patterns.sort(key=lambda x: (x["end_idx"] - x["start_idx"]) * x["width"], reverse=True)
        return patterns[:3]  # Max. 3 Ergebnisse
        
    return patterns


# 1. Render-Funktionen für Kanäle (channels.py)

def render_upward_channel(ax, df, pattern):
    """
    Zeichnet einen aufwärtsgerichteten Kanal auf die Achse
    """
    # Extrahiere die Hauptpunkte des Patterns
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # X-Bereich für die Linien
    x_range = range(start_idx, end_idx + 1)

    # Berechne die y-Werte für die obere und untere Kanallinie
    upper_y = [pattern['upper_intercept'] + pattern['upper_slope'] * (x - start_idx) for x in x_range]
    lower_y = [pattern['lower_intercept'] + pattern['lower_slope'] * (x - start_idx) for x in x_range]

    # Zeichne die Kanallinien
    ax.plot(x_range, upper_y, color='red', linestyle='-', linewidth=2, alpha=0.7)
    ax.plot(x_range, lower_y, color='green', linestyle='-', linewidth=2, alpha=0.7)

    # Markiere Berührungspunkte, falls vorhanden
    if 'upper_points' in pattern:
        for point in pattern['upper_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    if 'lower_points' in pattern:
        for point in pattern['lower_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    # Bei bestätigten Patterns: Durchbruchspunkt und Kursziel zeichnen
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']

        # Unterscheide zwischen Ausbruch nach oben und unten
        if pattern.get('breakout_up'):
            ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                       color='lime', s=80, marker='^')
        elif pattern.get('breakout_down'):
            ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                       color='red', s=80, marker='v')

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Kanals)
        text_pos_x = (start_idx + end_idx) // 2
        mid_upper = pattern['upper_intercept'] + pattern['upper_slope'] * (text_pos_x - start_idx)
        mid_lower = pattern['lower_intercept'] + pattern['lower_slope'] * (text_pos_x - start_idx)
        text_pos_y = (mid_upper + mid_lower) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_downward_channel(ax, df, pattern):
    """
    Zeichnet einen abwärtsgerichteten Kanal auf die Achse
    """
    # Extrahiere die Hauptpunkte des Patterns
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # X-Bereich für die Linien
    x_range = range(start_idx, end_idx + 1)

    # Berechne die y-Werte für die obere und untere Kanallinie
    upper_y = [pattern['upper_intercept'] + pattern['upper_slope'] * (x - start_idx) for x in x_range]
    lower_y = [pattern['lower_intercept'] + pattern['lower_slope'] * (x - start_idx) for x in x_range]

    # Zeichne die Kanallinien
    ax.plot(x_range, upper_y, color='red', linestyle='-', linewidth=2, alpha=0.7)
    ax.plot(x_range, lower_y, color='green', linestyle='-', linewidth=2, alpha=0.7)

    # Markiere Berührungspunkte, falls vorhanden
    if 'upper_points' in pattern:
        for point in pattern['upper_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    if 'lower_points' in pattern:
        for point in pattern['lower_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    # Bei bestätigten Patterns: Durchbruchspunkt und Kursziel zeichnen
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']

        # Unterscheide zwischen Ausbruch nach oben und unten
        if pattern.get('breakout_up'):
            ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                       color='lime', s=80, marker='^')
        elif pattern.get('breakout_down'):
            ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                       color='red', s=80, marker='v')

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Kanals)
        text_pos_x = (pattern['start_idx'] + pattern['end_idx']) // 2
        mid_upper = pattern['upper_intercept'] + pattern['upper_slope'] * text_pos_x
        mid_lower = pattern['lower_intercept'] + pattern['lower_slope'] * text_pos_x
        text_pos_y = (mid_upper + mid_lower) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_channels_pattern(ax, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "upward_channel":
        render_upward_channel(ax, df, pattern)
    elif pattern_type == "downward_channel":
        render_downward_channel(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Channels: {pattern_type}")
