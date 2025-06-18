import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT WEDGES
# ==============================================================================

def detect_falling_wedge(df, config=None, timeframe="1d"):
    """
    Erkennt fallende Keile (bullishes Umkehrmuster in Abwärtstrend)
    
    Eigenschaften:
    - Fallende Widerstandslinie (oben) und fallende Unterstützungslinie (unten)
    - Untere Linie flacher als obere Linie (konvergierend)
    - Ausbruch nach oben signalisiert Trendumkehr

    🔻 Erkennt fallende Keile (Falling Wedge)

    📊 Pattern-Typ: Bullisches Umkehrmuster in Abwärtstrends

    🔍 Pattern-Eigenschaften:
        - Fallende obere Trendlinie (Widerstand)
        - Fallende untere Trendlinie (Unterstützung)
        - Untere Linie fällt flacher → Linien konvergieren
        - Volumen nimmt ab während der Formation
        - Ausbruch nach oben = Trendumkehr Signal

    ⚙️ Parameter:
        - df (DataFrame): OHLCV-Daten mit Integer-Index
        - config (dict, optional): Überschreibt Standard-Konfiguration
        - min_pattern_bars: Mindest-Balken für Pattern (default: 10)
        - max_pattern_bars: Maximal-Balken für Pattern (default: 100)
        - min_touches: Min. Berührungen pro Trendlinie (default: 2)
        timeframe (str): Zeitrahmen für Config-Lookup (default: "1d")

    🎯 Returns:
    list: Pattern-Dictionaries mit:
        - type: "falling_wedge"
        - start_idx/end_idx: Pattern-Grenzen
        - upper_slope/upper_intercept: Obere Trendlinie
        - lower_slope/lower_intercept: Untere Trendlinie
        - upper_points/lower_points: Berührungspunkte
        - confirmed: Bool - Ausbruch bestätigt
        - breakout_idx: Index des Ausbruchs (falls confirmed)
        - target: Kursziel (Pattern-Höhe über Ausbruch)
        - stop_loss: Stop-Loss Level

    💡 Trading-Kontext:
         In Abwärtstrends = bullisches Umkehrsignal
         In Aufwärtstrends = Konsolidierung vor Fortsetzung

    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("falling_wedge", PATTERN_CONFIGS.get("falling_wedge", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 100)  # Größere Spanne zulassen
    min_touches = config.get("min_touches", 2)  # Minimale Berührungen pro Linie

    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Nicht jeden möglichen Startpunkt prüfen, sondern in Schritten
    # (verbessert Performance und reduziert überlappende Muster)
    for i in range(0, len(df) - min_pattern_bars, min(20, len(df) // 10)):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length

            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()

            # Wenn weniger als 10 Punkte, überspringen
            if len(segment) < 10:
                continue

            # Einen vereinfachten Ansatz für die Trendlinien verwenden:
            # Nimm die höchsten Hochs und tiefsten Tiefs im Segment

            # Teile das Segment in 4 gleiche Teile
            quarter_length = len(segment) // 4
            if quarter_length == 0:
                continue

            segment_parts = [
                segment.iloc[:quarter_length],
                segment.iloc[quarter_length:2 * quarter_length],
                segment.iloc[2 * quarter_length:3 * quarter_length],
                segment.iloc[3 * quarter_length:]
            ]

            # Finde die höchsten Hochs in jedem Segment-Teil
            upper_points = []
            for idx, part in enumerate(segment_parts):
                if len(part) > 0:
                    high_idx = part['high'].idxmax()
                    upper_points.append((high_idx, df.loc[high_idx, 'high']))

            # Finde die tiefsten Tiefs in jedem Segment-Teil
            lower_points = []
            for idx, part in enumerate(segment_parts):
                if len(part) > 0:
                    low_idx = part['low'].idxmin()
                    lower_points.append((low_idx, df.loc[low_idx, 'low']))

            # Brauchen mindestens 2 Punkte für jede Linie
            if len(upper_points) < min_touches or len(lower_points) < min_touches:
                continue

            # Sortiere nach Index
            upper_points.sort(key=lambda x: x[0])
            lower_points.sort(key=lambda x: x[0])

            # Lineare Regression für obere Linie
            upper_x = np.array([df.index.get_loc(p[0]) for p in upper_points])
            upper_y = np.array([p[1] for p in upper_points])

            # Lineare Regression für untere Linie
            lower_x = np.array([df.index.get_loc(p[0]) for p in lower_points])
            lower_y = np.array([p[1] for p in lower_points])

            # Berechne Regressionslinien
            try:
                upper_slope, upper_intercept = np.polyfit(upper_x, upper_y, 1)
                lower_slope, lower_intercept = np.polyfit(lower_x, lower_y, 1)
            except:
                continue  # Falls Regression fehlschlägt

            # Für fallenden Keil: beide Linien sollten abwärts geneigt sein
            if upper_slope >= 0 or lower_slope >= 0:
                continue

            # Untere Linie sollte flacher sein als obere Linie
            if abs(lower_slope) >= abs(upper_slope):
                continue

            # Prüfe, ob die Keile konvergieren
            start_idx_loc = df.index.get_loc(i)
            end_idx_loc = df.index.get_loc(end_idx)

            upper_start = upper_intercept + upper_slope * start_idx_loc
            lower_start = lower_intercept + lower_slope * start_idx_loc

            upper_end = upper_intercept + upper_slope * end_idx_loc
            lower_end = lower_intercept + lower_slope * end_idx_loc

            start_diff = upper_start - lower_start
            end_diff = upper_end - lower_end

            # Die Keile müssen am Ende enger sein als am Anfang
            if end_diff >= start_diff:
                continue

            # Minimale Breite am Anfang (als % des Preises)
            avg_price = df.iloc[i:end_idx + 1]['close'].mean()
            if start_diff < avg_price * 0.03:  # Mindestens 3% Breite
                continue

            # Prüfe auf Ausbruch über die obere Linie
            breakout_idx = None
            confirmed = False

            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                j_loc = df.index.get_loc(j)
                upper_proj = upper_intercept + upper_slope * j_loc

                if df.iloc[j]['close'] > upper_proj:
                    breakout_idx = j
                    confirmed = True
                    break

            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                # Umrechnen von DataFrame-Indizes in Arrays für die Visualisierung
                visual_upper_points = [(df.index.get_loc(p[0]) - df.index.get_loc(i), p[1]) for p in upper_points]
                visual_lower_points = [(df.index.get_loc(p[0]) - df.index.get_loc(i), p[1]) for p in lower_points]

                target = None
                if confirmed:
                    # Kursziel: Oft die Höhe des Anfangs des Keils
                    breakout_price = df.iloc[breakout_idx]['close']
                    target = breakout_price + start_diff * 0.8

                patterns.append({
                    "type": "falling_wedge",
                    "start_idx": i,
                    "end_idx": end_idx,
                    "upper_slope": upper_slope,
                    "upper_intercept": upper_intercept,
                    "lower_slope": lower_slope,
                    "lower_intercept": lower_intercept,
                    "upper_points": upper_points,
                    "lower_points": lower_points,
                    "visual_upper_points": visual_upper_points,
                    "visual_lower_points": visual_lower_points,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target
                })

    # Sortiere nach Qualität und begrenze die Anzahl
    if patterns:
        # Sortiere nach Länge des Musters (längere zuerst)
        patterns.sort(key=lambda x: x["end_idx"] - x["start_idx"], reverse=True)
        # Maximal 3 Muster zurückgeben
        return patterns[:3]

    return patterns


def detect_rising_wedge(df, config=None, timeframe="1d"):
    """
    Erkennt steigende Keile (bearishes Umkehrmuster in Aufwärtstrend)
    
    Eigenschaften:
    - Steigende Widerstandslinie (oben) und steigende Unterstützungslinie (unten)
    - Obere Linie flacher als untere Linie (konvergierend)
    - Ausbruch nach unten signalisiert Trendumkehr

    NEU
    🔺 Erkennt steigende Keile (Rising Wedge)

    📊 Pattern-Typ: Bearisches Umkehrmuster in Aufwärtstrends

    🔍 Pattern-Eigenschaften:
    - Steigende obere Trendlinie (Widerstand)
    - Steigende untere Trendlinie (Unterstützung)
    - Obere Linie steigt flacher → Linien konvergieren
    - Volumen nimmt ab während Formation
    - Ausbruch nach unten = Trendumkehr Signal

    ⚙️ Parameter:
        df (DataFrame): OHLCV-Daten mit Integer-Index
        config (dict, optional): Pattern-spezifische Konfiguration
        timeframe (str): Zeitrahmen-Kontext

    🎯 Returns:
        list: Analog zu falling_wedge, aber für steigende Keile

    💡 Trading-Kontext:
    In Aufwärtstrends = bearisches Umkehrsignal
    Oft am Ende von längeren Bullenmärkten
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("rising_wedge", PATTERN_CONFIGS.get("rising_wedge", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 10)
    max_pattern_bars = config.get("max_pattern_bars", 100)  # Größere Spanne zulassen
    min_touches = config.get("min_touches", 2)  # Minimale Berührungen pro Linie

    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Nicht jeden möglichen Startpunkt prüfen, sondern in Schritten
    # (verbessert Performance und reduziert überlappende Muster)
    for i in range(0, len(df) - min_pattern_bars, min(20, len(df) // 10)):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length

            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()

            # Wenn weniger als 10 Punkte, überspringen
            if len(segment) < 10:
                continue

            # Einen vereinfachten Ansatz für die Trendlinien verwenden:
            # Nimm die höchsten Hochs und tiefsten Tiefs im Segment

            # Teile das Segment in 4 gleiche Teile
            quarter_length = len(segment) // 4
            if quarter_length == 0:
                continue

            segment_parts = [
                segment.iloc[:quarter_length],
                segment.iloc[quarter_length:2 * quarter_length],
                segment.iloc[2 * quarter_length:3 * quarter_length],
                segment.iloc[3 * quarter_length:]
            ]

            # Finde die höchsten Hochs in jedem Segment-Teil
            upper_points = []
            for idx, part in enumerate(segment_parts):
                if len(part) > 0:
                    high_idx_pos = part['high'].values.argmax()
                    high_idx = part.index[high_idx_pos]
                    upper_points.append((high_idx, df.loc[high_idx, 'high']))

            # Finde die tiefsten Tiefs in jedem Segment-Teil
            lower_points = []
            for idx, part in enumerate(segment_parts):
                if len(part) > 0:
                    low_idx = part['low'].idxmin()
                    lower_points.append((low_idx, df.loc[low_idx, 'low']))

            # Brauchen mindestens 2 Punkte für jede Linie
            if len(upper_points) < min_touches or len(lower_points) < min_touches:
                continue

            # Sortiere nach Index
            upper_points.sort(key=lambda x: x[0])
            lower_points.sort(key=lambda x: x[0])

            # Lineare Regression für obere Linie
            upper_x = np.array([df.index.get_loc(p[0]) for p in upper_points])
            upper_y = np.array([p[1] for p in upper_points])

            # Lineare Regression für untere Linie
            lower_x = np.array([df.index.get_loc(p[0]) for p in lower_points])
            lower_y = np.array([p[1] for p in lower_points])

            # Berechne Regressionslinien
            try:
                upper_slope, upper_intercept = np.polyfit(upper_x, upper_y, 1)
                lower_slope, lower_intercept = np.polyfit(lower_x, lower_y, 1)
            except:
                continue  # Falls Regression fehlschlägt

            # Für steigenden Keil: beide Linien sollten aufwärts geneigt sein
            if upper_slope <= 0 or lower_slope <= 0:
                continue

            # Obere Linie sollte flacher sein als untere Linie
            if upper_slope >= lower_slope:
                continue

            # Prüfe, ob die Keile konvergieren
            start_idx_loc = df.index.get_loc(i)
            end_idx_loc = df.index.get_loc(end_idx)

            upper_start = upper_intercept + upper_slope * start_idx_loc
            lower_start = lower_intercept + lower_slope * start_idx_loc

            upper_end = upper_intercept + upper_slope * end_idx_loc
            lower_end = lower_intercept + lower_slope * end_idx_loc

            start_diff = upper_start - lower_start
            end_diff = upper_end - lower_end

            # Die Keile müssen am Ende enger sein als am Anfang
            if end_diff >= start_diff:
                continue

            # Minimale Breite am Anfang (als % des Preises)
            avg_price = df.iloc[i:end_idx + 1]['close'].mean()
            if start_diff < avg_price * 0.03:  # Mindestens 3% Breite
                continue

            # Prüfe auf Ausbruch unter die untere Linie
            breakout_idx = None
            confirmed = False

            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                j_loc = df.index.get_loc(j)
                lower_proj = lower_intercept + lower_slope * j_loc

                if df.iloc[j]['close'] < lower_proj:
                    breakout_idx = j
                    confirmed = True
                    break

            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                # Umrechnen von DataFrame-Indizes in Arrays für die Visualisierung
                visual_upper_points = [(df.index.get_loc(p[0]) - df.index.get_loc(i), p[1]) for p in upper_points]
                visual_lower_points = [(df.index.get_loc(p[0]) - df.index.get_loc(i), p[1]) for p in lower_points]

                target = None
                if confirmed:
                    # Kursziel: Oft die Höhe des Anfangs des Keils
                    breakout_price = df.iloc[breakout_idx]['close']
                    target = breakout_price - start_diff * 0.8

                patterns.append({
                    "type": "rising_wedge",
                    "start_idx": i,
                    "end_idx": end_idx,
                    "upper_slope": upper_slope,
                    "upper_intercept": upper_intercept,
                    "lower_slope": lower_slope,
                    "lower_intercept": lower_intercept,
                    "upper_points": upper_points,
                    "lower_points": lower_points,
                    "visual_upper_points": visual_upper_points,
                    "visual_lower_points": visual_lower_points,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target
                })

    # Sortiere nach Qualität und begrenze die Anzahl
    if patterns:
        # Sortiere nach Länge des Musters (längere zuerst)
        patterns.sort(key=lambda x: x["end_idx"] - x["start_idx"], reverse=True)
        # Maximal 3 Muster zurückgeben
        return patterns[:3]

    return patterns


# ==============================================================================
#                      RENDER WEDGES IN MATPLOTLIB
# ==============================================================================

def render_falling_wedge(ax, df, pattern):
    """
    🎨 Visualisiert fallenden Keil auf Chart-Achse

    ⚙️ Parameter:
        ax (matplotlib.Axes): Chart-Achse für Zeichnung
        df (DataFrame): Basis-Datensatz
        pattern (dict): Pattern-Dict von detect_falling_wedge()

    🎨 Zeichnet:
        - Rote obere Trendlinie (Widerstand)
        - Grüne untere Trendlinie (Unterstützung)
        - Berührungspunkte als Scatter-Plots
        - Ausbruchspunkt bei confirmed=True
        - Gestrichelte Kursziel-Linie
        - Optional: Stärke-Indikator (falls SHOW_STRENGTH_IN_CHART=True)
    """
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # X-Bereich für die Linien
    x_range = range(start_idx, end_idx + 1)

    # Obere und untere Trendlinie
    if 'upper_slope' in pattern and 'upper_intercept' in pattern:
        # Berechne die y-Werte für jede Linie
        # Muss angepasst werden, wenn die Indizes im DataFrame nicht fortlaufend sind
        upper_y = []
        lower_y = []

        # Indizes in DataFrame-Positionen konvertieren
        for x in x_range:
            idx_pos = df.index.get_loc(x) if x in df.index else x
            # Obere Linie
            upper_y.append(pattern['upper_intercept'] + pattern['upper_slope'] * idx_pos)
            # Untere Linie
            lower_y.append(pattern['lower_intercept'] + pattern['lower_slope'] * idx_pos)

        # Zeichne die Linien
        ax.plot(x_range, upper_y, color='#DC143C', linewidth=1, alpha=0.5)
        ax.plot(x_range, lower_y, color='#2E8B57', linewidth=1, alpha=0.5)

        # Zeichne auch Berührungspunkte, falls vorhanden
        if 'upper_points' in pattern:
            for point in pattern['upper_points']:
                point_idx = point[0]
                point_val = point[1]
                ax.scatter(point_idx, point_val, color='#DC143C', s=60, marker='o', alpha=0.8)

        if 'lower_points' in pattern:
            for point in pattern['lower_points']:
                point_idx = point[0]
                point_val = point[1]
                ax.scatter(point_idx, point_val, color='#2E8B57', s=60, marker='o', alpha=0.8)

        # Zeichne Ausbruchspunkt
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

            # Position für Stärke-Anzeige (Mitte des Keils)
            text_pos_x = (start_idx + end_idx) // 2
            idx_pos = df.index.get_loc(text_pos_x) if text_pos_x in df.index else text_pos_x
            upper_mid = pattern['upper_intercept'] + pattern['upper_slope'] * idx_pos
            lower_mid = pattern['lower_intercept'] + pattern['lower_slope'] * idx_pos
            text_pos_y = (upper_mid + lower_mid) / 2

            # Größe und Transparenz je nach Stärke
            text_size = 8 + int(strength * 4)
            text_alpha = 0.5 + (strength * 0.5)

            # Stärke als Text anzeigen
            ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                    fontsize=text_size, alpha=text_alpha, color='white',
                    bbox=dict(facecolor='green', alpha=0.3))


def render_rising_wedge(ax, df, pattern):
    """
    🎨 Visualisiert steigenden Keil auf Chart-Achse

    Analog zu render_falling_wedge() aber für steigende Keile
    Gleiche Visualisierungs-Elemente, angepasste Farben/Richtungen
    """
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # X-Bereich für die Linien
    x_range = range(start_idx, end_idx + 1)

    # Obere und untere Trendlinie
    if 'upper_slope' in pattern and 'upper_intercept' in pattern:
        # Berechne die y-Werte für jede Linie
        upper_y = []
        lower_y = []

        # Indizes in DataFrame-Positionen konvertieren
        for x in x_range:
            idx_pos = df.index.get_loc(x) if x in df.index else x
            # Obere Linie
            upper_y.append(pattern['upper_intercept'] + pattern['upper_slope'] * idx_pos)
            # Untere Linie
            lower_y.append(pattern['lower_intercept'] + pattern['lower_slope'] * idx_pos)

        # Zeichne die Linien
        ax.plot(x_range, upper_y, color='#DC143C', linewidth=1, alpha=0.5)
        ax.plot(x_range, lower_y, color='#2E8B57', linewidth=1, alpha=0.5)

        # Berührungspunkte zeichnen
        if 'upper_points' in pattern:
            for point in pattern['upper_points']:
                point_idx = point[0]
                point_val = point[1]
                ax.scatter(point_idx, point_val, color='#DC143C', s=60, marker='o', alpha=0.8)

        if 'lower_points' in pattern:
            for point in pattern['lower_points']:
                point_idx = point[0]
                point_val = point[1]
                ax.scatter(point_idx, point_val, color='#2E8B57', s=60, marker='o', alpha=0.8)

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

        # Position für Stärke-Anzeige (Mitte des Keils)
        text_pos_x = (start_idx + end_idx) // 2
        idx_pos = df.index.get_loc(text_pos_x) if text_pos_x in df.index else text_pos_x
        upper_mid = pattern['upper_intercept'] + pattern['upper_slope'] * idx_pos
        lower_mid = pattern['lower_intercept'] + pattern['lower_slope'] * idx_pos
        text_pos_y = (upper_mid + lower_mid) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_wedges(ax, df, pattern):
    """
    Rendert ein V- oder Cup-Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "falling_wedge":
        render_falling_wedge(ax, df, pattern)
    elif pattern_type == "rising_wedge":
        detect_rising_wedge(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Wedges: {pattern_type}")

# ==============================================================================
#                      RENDER WEDGES IN PLOTLY
# ==============================================================================

# Pattern-spezifische Plotly Renderer definieren...
def render_falling_wedge_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass

# Pattern-spezifische Plotly Renderer definieren...
def render_rising_wedge_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", 'unknown')

    if pattern_type == "falling_wedge":
        render_falling_wedge_plotly(fig, df, pattern)
    elif pattern_type == "rising_wedge":
        render_rising_wedge_plotly(fig, df, pattern)
    # ... weitere Pattern-Typen in dieser Datei ...
    else:
        print(f"Unbekannter Pattern-Typ für DATEI_NAME (Plotly): {pattern_type}")