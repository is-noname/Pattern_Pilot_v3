import pandas as pd
import numpy as np
from werkzeug.debug.tbtools import HEADER

from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT TRIANGLES
# ==============================================================================

def detect_ascending_triangle(df, config=None, timeframe="1d"):
    """
    Erkennt aufsteigende Dreiecke (bullishes Fortsetzungsmuster)
    
    Eigenschaften:
    - Horizontale Widerstandslinie (oben)
    - Aufsteigende Unterstützungslinie (unten)
    - Erwarteter Ausbruch nach oben

    NEU
    📈 Erkennt aufsteigende Dreiecke (Ascending Triangle)

    📊 Pattern-Typ: Bullisches Fortsetzungsmuster

    🔍 Pattern-Eigenschaften:
    - Horizontaler Widerstand (obere Begrenzung)
    - Steigende Unterstützungslinie (untere Begrenzung)
    - Käufer werden aggressiver bei jedem Rücksetzer
    - Verkäufer verteidigen konstantes Widerstandslevel
    - Ausbruch nach oben wahrscheinlich (≈70%)

    ⚙️ Parameter:
        df (DataFrame): OHLCV-Daten mit Integer-Index
        config (dict, optional): Pattern-Konfiguration
            - lookback_periods: Suchradius für lokale Extrema (default: 5)
            - min_touches: Min. Berührungen pro Linie (default: 2)
            - min_pattern_bars: Min. Pattern-Länge (default: 10)
            - max_pattern_bars: Max. Pattern-Länge (default: 50)
        timeframe (str): Zeitrahmen für Config-Lookup

    🎯 Returns:
        list: Pattern-Dictionaries mit:
            - type: "ascending_triangle"
            - start_idx/end_idx: Pattern-Boundaries
            - resistance_level: Horizontaler Widerstand
            - support_slope/support_intercept: Unterstützungslinie
            - resistance_points/support_points: Berührungspunkte
            - confirmed: Ausbruch bestätigt
            - breakout_idx: Ausbruchsindex
            - target: Kursziel (Dreieck-Höhe über Widerstand)
            - stop_loss: Stop unterhalb Unterstützung

    💡 Trading-Setup:
    Entry: Ausbruch über Widerstand + Volumen-Anstieg
    Stop: Unter die letzte Unterstützungs-Berührung
    Target: Dreieck-Höhe projiziert über Widerstand
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("ascending_triangle", PATTERN_CONFIGS.get("ascending_triangle", {}), timeframe)

    lookback_periods = config.get("lookback_periods", 5)
    min_touches = config.get("min_touches", 2)  # Mindestanzahl Berührungen pro Linie
    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 50)

    if len(df) < min_pattern_bars + lookback_periods:
        return []  # Nicht genug Daten

    patterns = []

    # Für jedes potenzielle Dreieck
    for i in range(len(df) - min_pattern_bars):
        end_idx = min(i + max_pattern_bars, len(df) - 1)

        if end_idx - i < min_pattern_bars:
            continue

        segment = df.iloc[i:end_idx + 1].copy()
        highs = segment['high'].values
        lows = segment['low'].values

        # Finde potenzielle horizontale Widerstandslinie (obere Begrenzung)
        resistance_points = []
        resistance_level = None

        # Identifiziere lokale Hochs
        for j in range(lookback_periods, len(segment) - lookback_periods):
            is_high = True
            for k in range(1, lookback_periods + 1):
                if highs[j] < highs[j - k] or highs[j] < highs[j + k]:
                    is_high = False
                    break

            if is_high:
                resistance_points.append((j + i, highs[j]))  # Original-Index + Wert

        if len(resistance_points) < min_touches:
            continue

        # Prüfe, ob die Hochs auf etwa gleicher Höhe liegen (horizontale Linie)
        first_high = resistance_points[0][1]
        resistance_valid = True

        for _, high_val in resistance_points:
            if abs(high_val - first_high) / first_high > 0.02:  # 2% Toleranz
                resistance_valid = False
                break

        if not resistance_valid:
            continue

        resistance_level = sum(p[1] for p in resistance_points) / len(resistance_points)

        # Finde aufsteigende Unterstützungslinie
        # Einfacher Ansatz: Verbinde mindestens zwei aufsteigende Tiefs
        support_points = []

        # Identifiziere lokale Tiefs
        for j in range(lookback_periods, len(segment) - lookback_periods):
            is_low = True
            for k in range(1, lookback_periods + 1):
                if lows[j] > lows[j - k] or lows[j] > lows[j + k]:
                    is_low = False
                    break

            if is_low:
                support_points.append((j + i, lows[j]))  # Original-Index + Wert

        if len(support_points) < min_touches:
            continue

        # Sortiere nach Index
        support_points.sort(key=lambda x: x[0])

        # Prüfe auf aufsteigende Tiefs
        is_ascending = True
        for idx in range(1, len(support_points)):
            if support_points[idx][1] <= support_points[idx - 1][1]:
                is_ascending = False
                break

        if not is_ascending:
            continue

        # Berechne Unterstützungslinie
        x = [p[0] for p in support_points]
        y = [p[1] for p in support_points]

        # Lineare Regression für Unterstützungslinie
        n = len(support_points)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_xx = sum(x_i * x_i for x_i in x)

        # Steigung berechnen: m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        support_slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

        # Prüfe auf positive Steigung (aufsteigend)
        if support_slope <= 0:
            continue

        # y-Achsenabschnitt: b = (Σy - m*Σx) / n
        support_intercept = (sum_y - support_slope * sum_x) / n

        # Prüfe auf Ausbruch über die Widerstandslinie
        confirmed = False
        breakout_idx = None

        for j in range(end_idx + 1, min(len(df), end_idx + 20)):
            if df['close'].iloc[j] > resistance_level:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Widerstandslinie + Höhe an der breitesten Stelle des Dreiecks
                pattern_height = resistance_level - (support_slope * i + support_intercept)
                target = resistance_level + pattern_height

            patterns.append({
                "type": "ascending_triangle",
                "start_idx": i,
                "end_idx": end_idx,
                "resistance_level": resistance_level,
                "support_slope": support_slope,
                "support_intercept": support_intercept,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "support_points": support_points,
                "resistance_points": resistance_points,
                "stop_loss": min(lows[-5:]) * 0.98  # 2% unter dem letzten Tief im Dreieck
            })

    return patterns


def detect_descending_triangle(df, config=None, timeframe="1d"):
    """
    Erkennt absteigende Dreiecke (bearishes Fortsetzungsmuster)

    Eigenschaften:
    - Horizontale Unterstützungslinie (unten)
    - Absteigende Widerstandslinie (oben)
    - Erwarteter Ausbruch nach unten

    NEU
    📉 Erkennt absteigende Dreiecke (Descending Triangle)

    📊 Pattern-Typ: Bearisches Fortsetzungsmuster

    🔍 Pattern-Eigenschaften:
    - Horizontale Unterstützung (untere Begrenzung)
    - Fallende Widerstandslinie (obere Begrenzung)
    - Verkäufer werden aggressiver bei jedem Anstieg
    - Käufer verteidigen konstantes Unterstützungslevel
    - Ausbruch nach unten wahrscheinlich (≈70%)

    ⚙️ Parameter: Analog zu ascending_triangle

    🎯 Returns: Analog zu ascending_triangle,
               aber für bearische Ausbrüche

    💡 Trading-Setup:
    Entry: Durchbruch unter Unterstützung + Volumen
    Stop: Über die letzte Widerstands-Berührung
    Target: Dreieck-Höhe projiziert unter Unterstützung
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("descending_triangle", PATTERN_CONFIGS.get("descending_triangle", {}), timeframe)

    lookback_periods = config.get("lookback_periods", 5)
    min_touches = config.get("min_touches", 2)  # Mindestanzahl Berührungen pro Linie
    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 50)

    if len(df) < min_pattern_bars + lookback_periods:
        return []  # Nicht genug Daten

    patterns = []

    # Für jedes potenzielle Dreieck
    for i in range(len(df) - min_pattern_bars):
        end_idx = min(i + max_pattern_bars, len(df) - 1)

        if end_idx - i < min_pattern_bars:
            continue

        segment = df.iloc[i:end_idx + 1].copy()
        highs = segment['high'].values
        lows = segment['low'].values

        # Finde potenzielle horizontale Unterstützungslinie (untere Begrenzung)
        support_points = []
        support_level = None

        # Identifiziere lokale Tiefs
        for j in range(lookback_periods, len(segment) - lookback_periods):
            is_low = True
            for k in range(1, lookback_periods + 1):
                if lows[j] > lows[j - k] or lows[j] > lows[j + k]:
                    is_low = False
                    break

            if is_low:
                support_points.append((j + i, lows[j]))  # Original-Index + Wert

        if len(support_points) < min_touches:
            continue

        # Prüfe, ob die Tiefs auf etwa gleicher Höhe liegen (horizontale Linie)
        first_low = support_points[0][1]
        support_valid = True

        for _, low_val in support_points:
            if abs(low_val - first_low) / first_low > 0.02:  # 2% Toleranz
                support_valid = False
                break

        if not support_valid:
            continue

        support_level = sum(p[1] for p in support_points) / len(support_points)

        # Finde absteigende Widerstandslinie
        # Verbinde mindestens zwei absteigende Hochs
        resistance_points = []

        # Identifiziere lokale Hochs
        for j in range(lookback_periods, len(segment) - lookback_periods):
            is_high = True
            for k in range(1, lookback_periods + 1):
                if highs[j] < highs[j - k] or highs[j] < highs[j + k]:
                    is_high = False
                    break

            if is_high:
                resistance_points.append((j + i, highs[j]))  # Original-Index + Wert

        if len(resistance_points) < min_touches:
            continue

        # Sortiere nach Index
        resistance_points.sort(key=lambda x: x[0])

        # Prüfe auf absteigende Hochs
        is_descending = True
        for idx in range(1, len(resistance_points)):
            if resistance_points[idx][1] >= resistance_points[idx - 1][1]:
                is_descending = False
                break

        if not is_descending:
            continue

        # Berechne Widerstandslinie
        x = [p[0] for p in resistance_points]
        y = [p[1] for p in resistance_points]

        # Lineare Regression für Widerstandslinie
        n = len(resistance_points)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_xx = sum(x_i * x_i for x_i in x)

        # Steigung berechnen: m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        resistance_slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

        # Prüfe auf negative Steigung (absteigend)
        if resistance_slope >= 0:
            continue

        # y-Achsenabschnitt: b = (Σy - m*Σx) / n
        resistance_intercept = (sum_y - resistance_slope * sum_x) / n

        # Prüfe auf Ausbruch unter die Unterstützungslinie
        confirmed = False
        breakout_idx = None

        for j in range(end_idx + 1, min(len(df), end_idx + 20)):
            if df['close'].iloc[j] < support_level:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Unterstützungslinie - Höhe an der breitesten Stelle des Dreiecks
                pattern_height = (resistance_slope * i + resistance_intercept) - support_level
                target = support_level - pattern_height

            patterns.append({
                "type": "descending_triangle",
                "start_idx": i,
                "end_idx": end_idx,
                "support_level": support_level,
                "resistance_slope": resistance_slope,
                "resistance_intercept": resistance_intercept,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "support_points": support_points,
                "resistance_points": resistance_points,
                "stop_loss": max(highs[-5:]) * 1.02  # 2% über dem letzten Hoch im Dreieck
            })

    return patterns


def detect_symmetrical_triangle(df, config=None, timeframe="1d"):
    """
    Erkennt symmetrische Dreiecke (neutrales Fortsetzungsmuster)

    Eigenschaften:
    - Fallende Widerstandslinie (oben)
    - Steigende Unterstützungslinie (unten)
    - Konvergierende Linien mit ähnlichem Steigungswinkel
    - Ausbruchsrichtung oft in Richtung des vorherigen Trends

    NEU
    ⚖️ Erkennt symmetrische Dreiecke (Symmetrical Triangle)

    📊 Pattern-Typ: Neutrales Fortsetzungsmuster

    🔍 Pattern-Eigenschaften:
    - Fallende Widerstandslinie (obere Begrenzung)
    - Steigende Unterstützungslinie (untere Begrenzung)
    - Beide Linien konvergieren mit ähnlichem Winkel
    - Unentschieden zwischen Käufern und Verkäufern
    - Ausbruch-Richtung folgt meist Vortrend

    ⚙️ Parameter:
        Zusätzlich zu Standard-Triangle-Parametern:
        - angle_similarity: Ähnlichkeit der Steigungswinkel (default: 0.7)

    🎯 Returns:
        Pattern-Dict mit beiden Trendlinien-Informationen
        breakout_direction: 'up' oder 'down' bei Bestätigung

    💡 Trading-Setup:
    Neutral bis Ausbruch → dann Richtung des Ausbruchs folgen
    Höhere Vorsicht: Kann in beide Richtungen ausbrechen
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("symmetrical_triangle", PATTERN_CONFIGS.get("symmetrical_triangle", {}), timeframe)

    lookback_periods = config.get("lookback_periods", 5)
    min_touches = config.get("min_touches", 2)  # Mindestanzahl Berührungen pro Linie
    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 50)
    angle_similarity = config.get("angle_similarity", 0.7)  # Wie ähnlich die Steigungswinkel sein müssen

    if len(df) < min_pattern_bars + lookback_periods:
        return []  # Nicht genug Daten

    patterns = []

    # Für jedes potenzielle Dreieck
    for i in range(len(df) - min_pattern_bars):
        end_idx = min(i + max_pattern_bars, len(df) - 1)

        if end_idx - i < min_pattern_bars:
            continue

        segment = df.iloc[i:end_idx + 1].copy()
        highs = segment['high'].values
        lows = segment['low'].values

        # Finde Widerstandspunkte (obere Begrenzung)
        resistance_points = []

        # Identifiziere lokale Hochs
        for j in range(lookback_periods, len(segment) - lookback_periods):
            is_high = True
            for k in range(1, lookback_periods + 1):
                if highs[j] < highs[j - k] or highs[j] < highs[j + k]:
                    is_high = False
                    break

            if is_high:
                resistance_points.append((j + i, highs[j]))  # Original-Index + Wert

        # Finde Unterstützungspunkte (untere Begrenzung)
        support_points = []

        # Identifiziere lokale Tiefs
        for j in range(lookback_periods, len(segment) - lookback_periods):
            is_low = True
            for k in range(1, lookback_periods + 1):
                if lows[j] > lows[j - k] or lows[j] > lows[j + k]:
                    is_low = False
                    break

            if is_low:
                support_points.append((j + i, lows[j]))  # Original-Index + Wert

        # Prüfe, ob genügend Punkte für beide Linien vorhanden sind
        if len(resistance_points) < min_touches or len(support_points) < min_touches:
            continue

        # Sortiere Punkte nach Index
        resistance_points.sort(key=lambda x: x[0])
        support_points.sort(key=lambda x: x[0])

        # Prüfe auf fallende Hochs
        is_descending_resistance = True
        for idx in range(1, len(resistance_points)):
            if resistance_points[idx][1] >= resistance_points[idx - 1][1]:
                is_descending_resistance = False
                break

        # Prüfe auf steigende Tiefs
        is_ascending_support = True
        for idx in range(1, len(support_points)):
            if support_points[idx][1] <= support_points[idx - 1][1]:
                is_ascending_support = False
                break

        # Für symmetrisches Dreieck muss Widerstand fallen und Unterstützung steigen
        if not (is_descending_resistance and is_ascending_support):
            continue

        # Berechne Widerstandslinie
        resistance_x = [p[0] for p in resistance_points]
        resistance_y = [p[1] for p in resistance_points]

        # Berechne Unterstützungslinie
        support_x = [p[0] for p in support_points]
        support_y = [p[1] for p in support_points]

        # Lineare Regression für beide Linien
        try:
            # Widerstandslinie
            n_res = len(resistance_points)
            sum_x_res = sum(resistance_x)
            sum_y_res = sum(resistance_y)
            sum_xy_res = sum(x_i * y_i for x_i, y_i in zip(resistance_x, resistance_y))
            sum_xx_res = sum(x_i * x_i for x_i in resistance_x)
            resistance_slope = (n_res * sum_xy_res - sum_x_res * sum_y_res) / (
                        n_res * sum_xx_res - sum_x_res * sum_x_res)
            resistance_intercept = (sum_y_res - resistance_slope * sum_x_res) / n_res

            # Unterstützungslinie
            n_sup = len(support_points)
            sum_x_sup = sum(support_x)
            sum_y_sup = sum(support_y)
            sum_xy_sup = sum(x_i * y_i for x_i, y_i in zip(support_x, support_y))
            sum_xx_sup = sum(x_i * x_i for x_i in support_x)
            support_slope = (n_sup * sum_xy_sup - sum_x_sup * sum_y_sup) / (n_sup * sum_xx_sup - sum_x_sup * sum_x_sup)
            support_intercept = (sum_y_sup - support_slope * sum_x_sup) / n_sup
        except:
            continue  # Überspringe bei Rechenfehlern

        # Prüfe auf negative Widerstandssteigung und positive Unterstützungssteigung
        if resistance_slope >= 0 or support_slope <= 0:
            continue

        # Für symmetrisches Dreieck: Steigungen sollten ähnlich sein (in absoluten Werten)
        slope_ratio = abs(resistance_slope) / abs(support_slope)
        if slope_ratio < angle_similarity or slope_ratio > (1.0 / angle_similarity):
            continue

        # Berechne den Schnittpunkt der Linien
        # x = (b2 - b1) / (m1 - m2)
        try:
            intersection_x = (support_intercept - resistance_intercept) / (resistance_slope - support_slope)
            # Der Schnittpunkt sollte nicht zu weit weg sein
            if intersection_x < end_idx or intersection_x > end_idx + max_pattern_bars:
                continue
        except:
            continue  # Bei parallelen Linien (Division durch Null)

        # Prüfe auf Ausbruch (nach oben oder unten)
        confirmed = False
        breakout_idx = None
        breakout_direction = None

        for j in range(end_idx + 1, min(len(df), end_idx + 20)):
            proj_resistance = resistance_slope * j + resistance_intercept
            proj_support = support_slope * j + support_intercept

            if df['close'].iloc[j] > proj_resistance:
                confirmed = True
                breakout_idx = j
                breakout_direction = "up"
                break
            elif df['close'].iloc[j] < proj_support:
                confirmed = True
                breakout_idx = j
                breakout_direction = "down"
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Höhe des Dreiecks am Startpunkt
                start_height = (resistance_slope * i + resistance_intercept) - (support_slope * i + support_intercept)

                if breakout_direction == "up":
                    # Kursziel bei Ausbruch nach oben: Ausbruchspunkt + Höhe
                    target = df['close'].iloc[breakout_idx] + start_height
                else:
                    # Kursziel bei Ausbruch nach unten: Ausbruchspunkt - Höhe
                    target = df['close'].iloc[breakout_idx] - start_height

            patterns.append({
                "type": "symmetrical_triangle",
                "start_idx": i,
                "end_idx": end_idx,
                "resistance_slope": resistance_slope,
                "resistance_intercept": resistance_intercept,
                "support_slope": support_slope,
                "support_intercept": support_intercept,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "breakout_direction": breakout_direction,
                "target": target,
                "resistance_points": resistance_points,
                "support_points": support_points,
                "stop_loss": (min(lows[-5:]) * 0.98) if breakout_direction == "up" else (max(highs[-5:]) * 1.02)
            })

    return patterns


# ==============================================================================
#                      RENDER TRIANGLES IN MATPLOTLIB
# ==============================================================================

def render_ascending_triangle(ax, df, pattern):
    """
    Zeichnet ein aufsteigendes Dreieck auf die Achse
    """
    # Dreieck zeichnen
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # Horizontale Widerstandslinie
    ax.axhline(y=pattern['resistance_level'], color='r', linestyle='--', alpha=0.7,
               xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Aufsteigende Unterstützungslinie
    x_range = range(start_idx, end_idx + 1)
    support_y = [pattern['support_intercept'] + pattern['support_slope'] * x for x in x_range]
    ax.plot(x_range, support_y, 'g-', linewidth=2, alpha=0.7)

    # Berührungspunkte
    if 'support_points' in pattern:
        for point in pattern['support_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    if 'resistance_points' in pattern:
        for point in pattern['resistance_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    # Ausbruchspunkt
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

        # Position für Stärke-Anzeige (Mitte des Dreiecks)
        text_pos_x = (start_idx + end_idx) // 2
        text_pos_y = (pattern['resistance_level'] + pattern['support_intercept'] +
                      pattern['support_slope'] * text_pos_x) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_descending_triangle(ax, df, pattern):
    """
    Zeichnet ein absteigendes Dreieck auf die Achse
    """
    # Dreieck zeichnen
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # Horizontale Unterstützungslinie
    ax.axhline(y=pattern['support_level'], color='g', linestyle='--', alpha=0.7,
               xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Absteigende Widerstandslinie
    x_range = range(start_idx, end_idx + 1)
    resistance_y = [pattern['resistance_intercept'] + pattern['resistance_slope'] * x for x in x_range]
    ax.plot(x_range, resistance_y, 'r-', linewidth=2, alpha=0.7)

    # Berührungspunkte
    if 'resistance_points' in pattern:
        for point in pattern['resistance_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    if 'support_points' in pattern:
        for point in pattern['support_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    # Ausbruchspunkt
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                   color='red', s=80, marker='v')
        
        # Kursziel anzeigen
        if pattern['target'] is not None:
            # Gepunktete Linie zum Kursziel
            target_y = pattern['target']
            ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Dreiecks)
        text_pos_x = (start_idx + end_idx) // 2
        mid_y = (pattern['support_level'] + pattern['resistance_intercept'] +
                 pattern['resistance_slope'] * text_pos_x) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, mid_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_symmetrical_triangle(ax, df, pattern):
    """
    Zeichnet ein symmetrisches Dreieck auf die Achse
    """
    # Dreieck zeichnen
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # Obere Linie (fallend) - Widerstand
    x_range = range(start_idx, end_idx + 1)
    resistance_y = [pattern['resistance_intercept'] + pattern['resistance_slope'] * x for x in x_range]
    ax.plot(x_range, resistance_y, 'r-', linewidth=2, alpha=0.7)

    # Untere Linie (steigend) - Unterstützung
    support_y = [pattern['support_intercept'] + pattern['support_slope'] * x for x in x_range]
    ax.plot(x_range, support_y, 'g-', linewidth=2, alpha=0.7)

    # Berührungspunkte
    if 'resistance_points' in pattern:
        for point in pattern['resistance_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='red', s=60, marker='o', alpha=0.8)

    if 'support_points' in pattern:
        for point in pattern['support_points']:
            point_idx = point[0]
            point_val = point[1]
            ax.scatter(point_idx, point_val, color='green', s=60, marker='o', alpha=0.8)

    # Ausbruchspunkt
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        breakout_marker = '^' if pattern['breakout_direction'] == 'up' else 'v'
        breakout_color = 'lime' if pattern['breakout_direction'] == 'up' else 'red'
        
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                  color=breakout_color, s=80, marker=breakout_marker)
        
        # Kursziel anzeigen
        if pattern['target'] is not None:
            target_y = pattern['target']
            target_color = 'lime' if pattern['breakout_direction'] == 'up' else 'red'
            ax.axhline(y=target_y, color=target_color, linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (Mitte des Dreiecks)
        text_pos_x = (start_idx + end_idx) // 2
        text_pos_y = (pattern['resistance_intercept'] + pattern['resistance_slope'] * text_pos_x +
                      pattern['support_intercept'] + pattern['support_slope'] * text_pos_x) / 2

        # Farbe je nach Ausbruchsrichtung
        bg_color = 'green' if pattern.get('breakout_direction') == 'up' else 'red'
        if not pattern.get('confirmed'):
            bg_color = 'gray'  # Neutral bei unbestätigtem Muster

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor=bg_color, alpha=0.3))

# DEF REMDER PATTERN FEHLT ODERß


# ==============================================================================
#                      RENDER TRIANGLES IN PLOTLY
# ==============================================================================

def render_ascending_triangle_plotly(fig, df, pattern):
    """Plotly Version des Ascending Triangle Pattern Renderers"""
    # ... [Code hier] ...
    pass

def render_descending_triangle_plotly(fig, df, pattern):
    """Plotly Version des Descending Triangle Pattern Renderers"""
    # ... [Code hier] ...
    pass

def render_symmetrical_triangle_plotly(fig, df, pattern):
    """Plotly Version des Symmetrical Triangle Pattern Renderers"""
    # ... [Code hier] ...
    pass

def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", 'unknown')

    if pattern_type == "ascending_triangle":
        render_ascending_triangle_plotly(fig, df, pattern)
    elif pattern_type == "descending_triangle":
        render_descending_triangle_plotly(fig, df, pattern)
    elif pattern_type == "symmetrical_triangle":
        render_symmetrical_triangle_plotly(fig, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Triangles (Plotly): {pattern_type}")