import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS #, TODO PTRN_CONF get_pattern_config noch nciht drin aber in 0.3; scaut dann in PATTERN_CONFIGS nach

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT (INVERSE) HEAD 6 SHOULDERS
# ==============================================================================
def detect_head_and_shoulders(df, config=None, timeframe="1d"):
    """
    Erkennt Kopf-Schulter-Formationen (bearishes Umkehrmuster)
    
    Eigenschaften:
    - Drei Hochs, wobei das mittlere (Kopf) höher ist als die beiden äußeren (Schultern)
    - Signal für eine Trendumkehr von Aufwärts nach Abwärts
    - Durchbruch unter die Nackenlinie bestätigt das Muster
    """
    # Config laden
    if config is None:
        from config.pattern_settings import get_pattern_config #TODO PTRN_CONF wo is get_pattern_config hin war das in 3.1 noch da oder aus 1.2?
        config = get_pattern_config("head_and_shoulders", PATTERN_CONFIGS.get("head_and_shoulders", {}), timeframe)

    tolerance = config.get("tolerance", 0.05)
    lookback_periods = config.get("lookback_periods", 5)
    min_pattern_bars = config.get("min_pattern_bars", 10)

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
    # Brauchen mindestens 3 Tops für Kopf-Schulter
    if len(tops) < 3:
        return patterns

    # Suche nach Kopf-Schulter-Formationen
    for i in range(len(tops) - 2):
        left_shoulder_idx = tops[i]
        head_idx = tops[i + 1]
        right_shoulder_idx = tops[i + 2]

        # Prüfe: Head muss höher sein als beide Schultern
        if highs[head_idx] <= highs[left_shoulder_idx] or highs[head_idx] <= highs[right_shoulder_idx]:
            continue

        # Prüfe: Schultern sollten auf ähnlichem Niveau sein
        shoulder_diff = abs(highs[left_shoulder_idx] - highs[right_shoulder_idx]) / highs[left_shoulder_idx]
        if shoulder_diff > tolerance:
            continue

        # Finde Nackenlinien-Tiefs
        left_trough_range = range(left_shoulder_idx + 1, head_idx)
        right_trough_range = range(head_idx + 1, right_shoulder_idx)

        if not left_trough_range or not right_trough_range:
            continue

        left_trough_idx = left_shoulder_idx + 1 + np.argmin(df['low'].values[left_trough_range])
        right_trough_idx = head_idx + 1 + np.argmin(df['low'].values[right_trough_range])

        left_trough = df['low'].values[left_trough_idx]
        right_trough = df['low'].values[right_trough_idx]

        # Berechne Nackenlinie (kann leicht geneigt sein)
        dx = right_trough_idx - left_trough_idx
        if dx == 0:  # Verhindere Division durch Null
            continue

        neckline_slope = (right_trough - left_trough) / dx

        # Prüfe auf Durchbruch unter die Nackenlinie
        confirmed = False
        breakout_idx = None

        for j in range(right_shoulder_idx + 1, min(len(df), right_shoulder_idx + 20)):
            # Projiziere Nackenlinie an Position j
            projected_neckline = left_trough + neckline_slope * (j - left_trough_idx)
            if df['close'].values[j] < projected_neckline:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Nackenlinie - Höhe des Kopfes
                head_height = highs[head_idx] - ((left_trough + right_trough) / 2)
                target = df['close'].values[breakout_idx] - head_height

            patterns.append({
                "type": "head_and_shoulders",
                "left_shoulder": left_shoulder_idx,
                "head": head_idx,
                "right_shoulder": right_shoulder_idx,
                "left_trough": left_trough_idx,
                "right_trough": right_trough_idx,
                "neckline_slope": neckline_slope,
                "neckline_intercept": left_trough - neckline_slope * left_trough_idx,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": highs[head_idx] * 1.02  # 2% über dem Kopf
            })

    return patterns


def detect_inverse_head_and_shoulders(df, config=None, timeframe="1d"):
    """
    Erkennt inverse Kopf-Schulter-Formationen (bullishes Umkehrmuster)

    Eigenschaften:
    - Drei Tiefs, wobei das mittlere (Kopf) tiefer ist als die beiden äußeren (Schultern)
    - Signal für eine Trendumkehr von Abwärts nach Aufwärts
    - Durchbruch über die Nackenlinie bestätigt das Muster
    """
    # Config laden
    if config is None:
        from config.pattern_settings import get_pattern_config
        config = get_pattern_config("inverse_head_and_shoulders", PATTERN_CONFIGS.get("inverse_head_and_shoulders", {}),
                                    timeframe)

    tolerance = config.get("tolerance", 0.05)
    lookback_periods = config.get("lookback_periods", 5)
    min_pattern_bars = config.get("min_pattern_bars", 10)

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
    # Brauchen mindestens 3 Bottoms für inverse Kopf-Schulter
    if len(bottoms) < 3:
        return patterns

    # Suche nach inversen Kopf-Schulter-Formationen
    for i in range(len(bottoms) - 2):
        left_shoulder_idx = bottoms[i]
        head_idx = bottoms[i + 1]
        right_shoulder_idx = bottoms[i + 2]

        # Prüfe: Head muss tiefer sein als beide Schultern
        if lows[head_idx] >= lows[left_shoulder_idx] or lows[head_idx] >= lows[right_shoulder_idx]:
            continue

        # Prüfe: Schultern sollten auf ähnlichem Niveau sein
        shoulder_diff = abs(lows[left_shoulder_idx] - lows[right_shoulder_idx]) / abs(lows[left_shoulder_idx])
        if shoulder_diff > tolerance:
            continue

        # Finde Nackenlinien-Hochs
        left_peak_range = range(left_shoulder_idx + 1, head_idx)
        right_peak_range = range(head_idx + 1, right_shoulder_idx)

        if not left_peak_range or not right_peak_range:
            continue

        left_peak_idx = left_shoulder_idx + 1 + np.argmax(df['high'].values[left_peak_range])
        right_peak_idx = head_idx + 1 + np.argmax(df['high'].values[right_peak_range])

        left_peak = df['high'].values[left_peak_idx]
        right_peak = df['high'].values[right_peak_idx]

        # Berechne Nackenlinie (kann leicht geneigt sein)
        dx = right_peak_idx - left_peak_idx
        if dx == 0:  # Verhindere Division durch Null
            continue

        neckline_slope = (right_peak - left_peak) / dx

        # Prüfe auf Durchbruch über die Nackenlinie
        confirmed = False
        breakout_idx = None

        for j in range(right_shoulder_idx + 1, min(len(df), right_shoulder_idx + 20)):
            # Projiziere Nackenlinie an Position j
            projected_neckline = left_peak + neckline_slope * (j - left_peak_idx)
            if df['close'].values[j] > projected_neckline:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Nackenlinie + Höhe des Kopfes
                head_height = ((left_peak + right_peak) / 2) - lows[head_idx]
                target = df['close'].values[breakout_idx] + head_height

            patterns.append({
                "type": "inverse_head_and_shoulders",
                "left_shoulder": left_shoulder_idx,
                "head": head_idx,
                "right_shoulder": right_shoulder_idx,
                "left_peak": left_peak_idx,
                "right_peak": right_peak_idx,
                "neckline_slope": neckline_slope,
                "neckline_intercept": left_peak - neckline_slope * left_peak_idx,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": lows[head_idx] * 0.98  # 2% unter dem Kopf
            })

    return patterns

# ==============================================================================
#                      RENDER H&S IN MATPLOTLIB
# ==============================================================================
def render_head_and_shoulders(ax, df, pattern):
    """
    Zeichnet eine Head and Shoulders Formation auf die Achse
    """
    # Kopf und Schultern zeichnen
    ax.scatter(pattern['left_shoulder'], df['high'].iloc[pattern['left_shoulder']],
              color='red', s=100, marker='o')
    ax.scatter(pattern['head'], df['high'].iloc[pattern['head']],
              color='red', s=100, marker='o')
    ax.scatter(pattern['right_shoulder'], df['high'].iloc[pattern['right_shoulder']],
              color='red', s=100, marker='o')

    # Nackenlinie zeichnen (kann geneigt sein)
    x_range = range(pattern['left_trough'], pattern['right_trough'] + 1)
    neckline_y = [pattern['neckline_intercept'] + pattern['neckline_slope'] * x for x in x_range]
    ax.plot(x_range, neckline_y, 'r--', linewidth=2, alpha=0.7)

    # Ausbruchspunkt
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                  color='white', s=80, marker='v')

        # Kursziel, falls verfügbar
        if pattern['target'] is not None:
            # Gepunktete Linie zum Kursziel
            target_y = pattern['target']
            ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (unter dem Kopf)
        text_pos_x = pattern['head']
        text_pos_y = df['high'].iloc[pattern['head']] * 0.97

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)  # 8-12pt je nach Stärke
        text_alpha = 0.5 + (strength * 0.5)  # 0.5-1.0 Transparenz

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_inverse_head_and_shoulders(ax, df, pattern):
    """
    Zeichnet eine inverse Head and Shoulders Formation auf die Achse
    """
    # Kopf und Schultern zeichnen (in diesem Fall die Tiefs)
    ax.scatter(pattern['left_shoulder'], df['low'].iloc[pattern['left_shoulder']],
               color='lime', s=100, marker='o')
    ax.scatter(pattern['head'], df['low'].iloc[pattern['head']],
               color='lime', s=100, marker='o')
    ax.scatter(pattern['right_shoulder'], df['low'].iloc[pattern['right_shoulder']],
               color='lime', s=100, marker='o')

    # Nackenlinie zeichnen (kann geneigt sein)
    x_range = range(pattern['left_peak'], pattern['right_peak'] + 1)
    neckline_y = [pattern['neckline_intercept'] + pattern['neckline_slope'] * x for x in x_range]
    ax.plot(x_range, neckline_y, 'g--', linewidth=2, alpha=0.7)

    # Ausbruchspunkt
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                   color='lime', s=80, marker='^')

        # Kursziel, falls verfügbar
        if pattern['target'] is not None:
            # Gepunktete Linie zum Kursziel
            target_y = pattern['target']
            ax.axhline(y=target_y, color='lime', linestyle=':', alpha=0.5,
                       xmin=pattern['breakout_idx'] / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (über dem Kopf)
        text_pos_x = pattern['head']
        text_pos_y = df['low'].iloc[pattern['head']] * 0.96

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

    if pattern_type == "head_and_shoulders":
        render_head_and_shoulders(ax, df, pattern)
    elif pattern_type == "inverse_head_and_shoulders":
        render_inverse_head_and_shoulders(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ: {pattern_type}")
# ==============================================================================
#                      RENDER H&S IN PLOTLY
# ==============================================================================
def render_head_and_shoulders_plotly(fig, df, pattern):
    """Plotly Version des Head and Shoulders Pattern Renderers"""
    # ... [Code hier] ...
    pass


def render_inverse_head_and_shoulders_plotly(fig, df, pattern):
    """Plotly Version des Inverse Head and Shoulders Pattern Renderers"""
    # ... [Code hier] ...
    pass


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "head_and_shoulders":
        render_head_and_shoulders_plotly(fig, df, pattern)
    elif pattern_type == "inverse_head_and_shoulders":
        render_inverse_head_and_shoulders_plotly(fig, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Head-Shoulders (Plotly): {pattern_type}")



