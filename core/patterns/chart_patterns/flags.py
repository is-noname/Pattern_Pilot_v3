#import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


def detect_bullish_flag(df, config=None, timeframe="1d"):
    """
    Erkennt bullische Flaggen (Fortsetzungsmuster nach Aufwärtstrend)
    
    Eigenschaften:
    - Starker Aufwärtstrend ("Fahnenmast")
    - Kurze Konsolidierungsphase mit leicht abwärts geneigten parallelen Linien
    - Fortsetzung des Aufwärtstrends nach Durchbruch
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("bullish_flag", PATTERN_CONFIGS.get("bullish_flag", {}), timeframe)

    min_pole_bars = config.get("min_pole_bars", 5)
    max_pole_bars = config.get("max_pole_bars", 20)
    min_flag_bars = config.get("min_flag_bars", 5)
    max_flag_bars = config.get("max_flag_bars", 20)
    pole_rate_threshold = config.get("pole_rate_threshold", 0.5)  # Minimum Steigungsrate für Fahnenmast

    if len(df) < min_pole_bars + min_flag_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Suche nach starken Aufwärtstrends für den "Fahnenmast"
    for i in range(len(df) - min_pole_bars - min_flag_bars):
        # Prüfe auf starken Aufwärtstrend (Fahnenmast)
        pole_start = i
        pole_end = min(i + max_pole_bars, len(df) - min_flag_bars)

        # Suche nach dem besten Fahnenmast-Kandidaten
        best_pole_rate = 0
        best_pole_end = None

        for j in range(i + min_pole_bars, pole_end):
            pole_start_price = df['low'].iloc[i]
            pole_end_price = df['high'].iloc[j]
            pole_rate = (pole_end_price - pole_start_price) / (pole_start_price * (j - i))

            if pole_rate > best_pole_rate:
                best_pole_rate = pole_rate
                best_pole_end = j

        # Wenn kein ausreichend starker Fahnenmast gefunden wurde
        if best_pole_rate < pole_rate_threshold or best_pole_end is None:
            continue

        pole_end = best_pole_end
        pole_height = df['high'].iloc[pole_end] - df['low'].iloc[pole_start]

        # Suche nach der Flagge (Konsolidierung nach dem Fahnenmast)
        flag_start = pole_end
        flag_end = min(flag_start + max_flag_bars, len(df) - 1)

        # Flagge sollte eine leicht abwärts gerichtete Konsolidierung sein
        flag_segment = df.iloc[flag_start:flag_end + 1]

        # Berechne obere und untere Kanallinie für die Flagge
        highs = flag_segment['high'].values
        lows = flag_segment['low'].values

        # Lineare Regression für die Hochs
        x = np.array(range(len(highs)))
        if len(x) < min_flag_bars:
            continue

        # Obere Linie
        upper_slope, upper_intercept = np.polyfit(x, highs, 1)

        # Untere Linie
        lower_slope, lower_intercept = np.polyfit(x, lows, 1)

        # Für bullische Flagge sollten beide Linien leicht abwärts gerichtet sein
        if upper_slope >= 0 or lower_slope >= 0:
            continue

        # Linien sollten nahezu parallel sein
        if abs(upper_slope - lower_slope) > 0.1:  # Toleranzwert
            continue

        # Prüfe, ob Volumen während der Flaggenphase abnimmt (falls Volumen verfügbar)
        volume_confirms = True
        if 'volume' in df.columns:
            pole_volume = df['volume'].iloc[pole_start:pole_end + 1].mean()
            flag_volume = df['volume'].iloc[flag_start:flag_end + 1].mean()
            volume_confirms = flag_volume < pole_volume

        # Prüfe auf Ausbruch aus der Flagge
        confirmed = False
        breakout_idx = None

        for j in range(flag_end + 1, min(len(df), flag_end + 20)):
            # Projiziere obere Flaggenlinie
            projected_upper = upper_intercept + upper_slope * (j - flag_start)
            if df['close'].iloc[j] > projected_upper:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Höhe des Flaggenmasts vom Ausbruchspunkt projiziert
                target = df['close'].iloc[breakout_idx] + pole_height

            patterns.append({
                "type": "bullish_flag",
                "pole_start": pole_start,
                "pole_end": pole_end,
                "flag_start": flag_start,
                "flag_end": flag_end,
                "pole_height": pole_height,
                "upper_slope": upper_slope,
                "upper_intercept": upper_intercept,
                "lower_slope": lower_slope,
                "lower_intercept": lower_intercept,
                "volume_confirms": volume_confirms,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": min(lows) * 0.98  # 2% unter dem tiefsten Punkt der Flagge
            })

    return patterns


def detect_bearish_flag(df, config=None, timeframe="1d"):
    """
    Erkennt bearische Flaggen (Fortsetzungsmuster nach Abwärtstrend)
    
    Eigenschaften:
    - Starker Abwärtstrend ("Fahnenmast")
    - Kurze Konsolidierungsphase mit leicht aufwärts geneigten parallelen Linien
    - Fortsetzung des Abwärtstrends nach Durchbruch
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("bearish_flag", PATTERN_CONFIGS.get("bearish_flag", {}), timeframe)

    min_pole_bars = config.get("min_pole_bars", 5)
    max_pole_bars = config.get("max_pole_bars", 20)
    min_flag_bars = config.get("min_flag_bars", 5)
    max_flag_bars = config.get("max_flag_bars", 20)
    pole_rate_threshold = config.get("pole_rate_threshold", 0.5)  # Minimum Abfallrate für Fahnenmast

    if len(df) < min_pole_bars + min_flag_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Suche nach starken Abwärtstrends für den "Fahnenmast"
    for i in range(len(df) - min_pole_bars - min_flag_bars):
        # Prüfe auf starken Abwärtstrend (Fahnenmast)
        pole_start = i
        pole_end = min(i + max_pole_bars, len(df) - min_flag_bars)

        # Suche nach dem besten Fahnenmast-Kandidaten
        best_pole_rate = 0
        best_pole_end = None

        for j in range(i + min_pole_bars, pole_end):
            pole_start_price = df['high'].iloc[i]
            pole_end_price = df['low'].iloc[j]
            # Für Abwärtstrend betrachten wir den relativen Preisrückgang
            pole_rate = (pole_start_price - pole_end_price) / (pole_start_price * (j - i))

            if pole_rate > best_pole_rate:
                best_pole_rate = pole_rate
                best_pole_end = j

        # Wenn kein ausreichend starker Fahnenmast gefunden wurde
        if best_pole_rate < pole_rate_threshold or best_pole_end is None:
            continue

        pole_end = best_pole_end
        pole_height = df['high'].iloc[pole_start] - df['low'].iloc[pole_end]

        # Suche nach der Flagge (Konsolidierung nach dem Fahnenmast)
        flag_start = pole_end
        flag_end = min(flag_start + max_flag_bars, len(df) - 1)

        # Flagge sollte eine leicht aufwärts gerichtete Konsolidierung sein
        flag_segment = df.iloc[flag_start:flag_end + 1]

        # Berechne obere und untere Kanallinie für die Flagge
        highs = flag_segment['high'].values
        lows = flag_segment['low'].values

        # Lineare Regression für die Hochs
        x = np.array(range(len(highs)))
        if len(x) < min_flag_bars:
            continue

        # Obere Linie
        upper_slope, upper_intercept = np.polyfit(x, highs, 1)

        # Untere Linie
        lower_slope, lower_intercept = np.polyfit(x, lows, 1)

        # Für bearische Flagge sollten beide Linien leicht aufwärts gerichtet sein
        if upper_slope <= 0 or lower_slope <= 0:
            continue

        # Linien sollten nahezu parallel sein
        if abs(upper_slope - lower_slope) > 0.1:  # Toleranzwert
            continue

        # Prüfe, ob Volumen während der Flaggenphase abnimmt (falls Volumen verfügbar)
        volume_confirms = True
        if 'volume' in df.columns:
            pole_volume = df['volume'].iloc[pole_start:pole_end + 1].mean()
            flag_volume = df['volume'].iloc[flag_start:flag_end + 1].mean()
            volume_confirms = flag_volume < pole_volume

        # Prüfe auf Ausbruch aus der Flagge (nach unten)
        confirmed = False
        breakout_idx = None

        for j in range(flag_end + 1, min(len(df), flag_end + 20)):
            # Projiziere untere Flaggenlinie
            projected_lower = lower_intercept + lower_slope * (j - flag_start)
            if df['close'].iloc[j] < projected_lower:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Höhe des Flaggenmasts vom Ausbruchspunkt projiziert (nach unten)
                target = df['close'].iloc[breakout_idx] - pole_height

            patterns.append({
                "type": "bearish_flag",
                "pole_start": pole_start,
                "pole_end": pole_end,
                "flag_start": flag_start,
                "flag_end": flag_end,
                "pole_height": pole_height,
                "upper_slope": upper_slope,
                "upper_intercept": upper_intercept,
                "lower_slope": lower_slope,
                "lower_intercept": lower_intercept,
                "volume_confirms": volume_confirms,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": max(highs) * 1.02  # 2% über dem höchsten Punkt der Flagge
            })

    return patterns


def detect_bullish_pennant(df, config=None, timeframe="1d"):
    """
    Erkennt bullische Wimpel (ähnlich einer Flagge, aber mit konvergierenden Linien)
    
    Eigenschaften:
    - Starker Aufwärtstrend ("Fahnenmast")
    - Kurze Konsolidierungsphase mit konvergierenden Linien (Dreieck)
    - Typischerweise kürzer als ein symmetrisches Dreieck
    - Fortsetzung des Aufwärtstrends nach Durchbruch
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("bullish_pennant", PATTERN_CONFIGS.get("bullish_pennant", {}), timeframe)

    min_pole_bars = config.get("min_pole_bars", 5)
    max_pole_bars = config.get("max_pole_bars", 20)
    min_pennant_bars = config.get("min_pennant_bars", 5)
    max_pennant_bars = config.get("max_pennant_bars", 15)  # Pennants sind typischerweise kürzer als Dreiecke
    pole_rate_threshold = config.get("pole_rate_threshold", 0.5)  # Minimum Steigungsrate für Fahnenmast

    if len(df) < min_pole_bars + min_pennant_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Suche nach starken Aufwärtstrends für den "Fahnenmast"
    for i in range(len(df) - min_pole_bars - min_pennant_bars):
        # Prüfe auf starken Aufwärtstrend (Fahnenmast)
        pole_start = i
        pole_end = min(i + max_pole_bars, len(df) - min_pennant_bars)

        # Suche nach dem besten Fahnenmast-Kandidaten
        best_pole_rate = 0
        best_pole_end = None

        for j in range(i + min_pole_bars, pole_end):
            pole_start_price = df['low'].iloc[i]
            pole_end_price = df['high'].iloc[j]
            pole_rate = (pole_end_price - pole_start_price) / (pole_start_price * (j - i))

            if pole_rate > best_pole_rate:
                best_pole_rate = pole_rate
                best_pole_end = j

        # Wenn kein ausreichend starker Fahnenmast gefunden wurde
        if best_pole_rate < pole_rate_threshold or best_pole_end is None:
            continue

        pole_end = best_pole_end
        pole_height = df['high'].iloc[pole_end] - df['low'].iloc[pole_start]

        # Suche nach dem Wimpel (Konsolidierung nach dem Fahnenmast)
        pennant_start = pole_end
        pennant_end = min(pennant_start + max_pennant_bars, len(df) - 1)

        # Wimpel sollte eine Konsolidierung mit konvergierenden Linien sein
        pennant_segment = df.iloc[pennant_start:pennant_end + 1]

        # Berechne obere und untere Begrenzungslinien für den Wimpel
        highs = pennant_segment['high'].values
        lows = pennant_segment['low'].values

        # Prüfe, ob genügend Daten für die Regression vorhanden sind
        if len(highs) < min_pennant_bars:
            continue

        # Lineare Regression für die Hochs
        x_high = np.array(range(len(highs)))
        upper_slope, upper_intercept = np.polyfit(x_high, highs, 1)

        # Lineare Regression für die Tiefs
        x_low = np.array(range(len(lows)))
        lower_slope, lower_intercept = np.polyfit(x_low, lows, 1)

        # Für Wimpel: Obere Linie fallend, untere Linie steigend oder weniger fallend
        if not (upper_slope < 0 and lower_slope > upper_slope):
            continue

        # Prüfe, ob die Linien konvergieren
        if upper_slope >= lower_slope:
            continue

        # Prüfe, ob Volumen während der Wimpelphase abnimmt (falls Volumen verfügbar)
        volume_confirms = True
        if 'volume' in df.columns:
            pole_volume = df['volume'].iloc[pole_start:pole_end + 1].mean()
            pennant_volume = df['volume'].iloc[pennant_start:pennant_end + 1].mean()
            volume_confirms = pennant_volume < pole_volume

        # Prüfe auf Ausbruch aus dem Wimpel (nach oben)
        confirmed = False
        breakout_idx = None

        for j in range(pennant_end + 1, min(len(df), pennant_end + 20)):
            # Projiziere obere Wimpellinie
            days_after_start = j - pennant_start
            projected_upper = upper_intercept + upper_slope * days_after_start
            if df['close'].iloc[j] > projected_upper:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Höhe des Fahnenmasts vom Ausbruchspunkt projiziert
                target = df['close'].iloc[breakout_idx] + pole_height

            patterns.append({
                "type": "bullish_pennant",
                "pole_start": pole_start,
                "pole_end": pole_end,
                "pennant_start": pennant_start,
                "pennant_end": pennant_end,
                "pole_height": pole_height,
                "upper_slope": upper_slope,
                "upper_intercept": upper_intercept,
                "lower_slope": lower_slope,
                "lower_intercept": lower_intercept,
                "volume_confirms": volume_confirms,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": min(lows) * 0.98  # 2% unter dem tiefsten Punkt des Wimpels
            })

    return patterns


def detect_bearish_pennant(df, config=None, timeframe="1d"):
    """
    Erkennt bearische Wimpel (ähnlich einer Flagge, aber mit konvergierenden Linien)
    
    Eigenschaften:
    - Starker Abwärtstrend ("Fahnenmast")
    - Kurze Konsolidierungsphase mit konvergierenden Linien (Dreieck)
    - Typischerweise kürzer als ein symmetrisches Dreieck
    - Fortsetzung des Abwärtstrends nach Durchbruch
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("bearish_pennant", PATTERN_CONFIGS.get("bearish_pennant", {}), timeframe)

    min_pole_bars = config.get("min_pole_bars", 5)
    max_pole_bars = config.get("max_pole_bars", 20)
    min_pennant_bars = config.get("min_pennant_bars", 5)
    max_pennant_bars = config.get("max_pennant_bars", 15)  # Pennants sind typischerweise kürzer als Dreiecke
    pole_rate_threshold = config.get("pole_rate_threshold", 0.5)  # Minimum Abfallrate für Fahnenmast

    if len(df) < min_pole_bars + min_pennant_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Suche nach starken Abwärtstrends für den "Fahnenmast"
    for i in range(len(df) - min_pole_bars - min_pennant_bars):
        # Prüfe auf starken Abwärtstrend (Fahnenmast)
        pole_start = i
        pole_end = min(i + max_pole_bars, len(df) - min_pennant_bars)

        # Suche nach dem besten Fahnenmast-Kandidaten
        best_pole_rate = 0
        best_pole_end = None

        for j in range(i + min_pole_bars, pole_end):
            pole_start_price = df['high'].iloc[i]
            pole_end_price = df['low'].iloc[j]
            # Für Abwärtstrend betrachten wir den relativen Preisrückgang
            pole_rate = (pole_start_price - pole_end_price) / (pole_start_price * (j - i))

            if pole_rate > best_pole_rate:
                best_pole_rate = pole_rate
                best_pole_end = j

        # Wenn kein ausreichend starker Fahnenmast gefunden wurde
        if best_pole_rate < pole_rate_threshold or best_pole_end is None:
            continue

        pole_end = best_pole_end
        pole_height = df['high'].iloc[pole_start] - df['low'].iloc[pole_end]

        # Suche nach dem Wimpel (Konsolidierung nach dem Fahnenmast)
        pennant_start = pole_end
        pennant_end = min(pennant_start + max_pennant_bars, len(df) - 1)

        # Wimpel sollte eine Konsolidierung mit konvergierenden Linien sein
        pennant_segment = df.iloc[pennant_start:pennant_end + 1]

        # Berechne obere und untere Begrenzungslinien für den Wimpel
        highs = pennant_segment['high'].values
        lows = pennant_segment['low'].values

        # Prüfe, ob genügend Daten für die Regression vorhanden sind
        if len(highs) < min_pennant_bars:
            continue

        # Lineare Regression für die Hochs
        x_high = np.array(range(len(highs)))
        upper_slope, upper_intercept = np.polyfit(x_high, highs, 1)

        # Lineare Regression für die Tiefs
        x_low = np.array(range(len(lows)))
        lower_slope, lower_intercept = np.polyfit(x_low, lows, 1)

        # Für bearischen Wimpel: Obere Linie steigend oder weniger fallend, untere Linie fallend
        if not (lower_slope < 0 and upper_slope > lower_slope):
            continue

        # Prüfe, ob die Linien konvergieren
        if upper_slope <= lower_slope:
            continue

        # Prüfe, ob Volumen während der Wimpelphase abnimmt (falls Volumen verfügbar)
        volume_confirms = True
        if 'volume' in df.columns:
            pole_volume = df['volume'].iloc[pole_start:pole_end + 1].mean()
            pennant_volume = df['volume'].iloc[pennant_start:pennant_end + 1].mean()
            volume_confirms = pennant_volume < pole_volume

        # Prüfe auf Ausbruch aus dem Wimpel (nach unten)
        confirmed = False
        breakout_idx = None

        for j in range(pennant_end + 1, min(len(df), pennant_end + 20)):
            # Projiziere untere Wimpellinie
            days_after_start = j - pennant_start
            projected_lower = lower_intercept + lower_slope * days_after_start
            if df['close'].iloc[j] < projected_lower:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Höhe des Fahnenmasts vom Ausbruchspunkt projiziert (nach unten)
                target = df['close'].iloc[breakout_idx] - pole_height

            patterns.append({
                "type": "bearish_pennant",
                "pole_start": pole_start,
                "pole_end": pole_end,
                "pennant_start": pennant_start,
                "pennant_end": pennant_end,
                "pole_height": pole_height,
                "upper_slope": upper_slope,
                "upper_intercept": upper_intercept,
                "lower_slope": lower_slope,
                "lower_intercept": lower_intercept,
                "volume_confirms": volume_confirms,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": max(highs) * 1.02  # 2% über dem höchsten Punkt des Wimpels
            })

    return patterns


def render_bullish_flag(ax, df, pattern):
    """
    Zeichnet ein bullisches Flaggen-Muster auf die Achse
    """
    # Fahnenmast zeichnen
    pole_start = pattern['pole_start']
    pole_end = pattern['pole_end']
    ax.plot([pole_start, pole_end],
            [df['low'].iloc[pole_start], df['high'].iloc[pole_end]],
            'g-', linewidth=3, alpha=0.7)

    # Flaggenkanal zeichnen
    flag_start = pattern['flag_start']
    flag_end = pattern['flag_end']

    # Berechne die Flaggenkanallinien
    x_range = range(flag_start, flag_end + 1)
    upper_y = [pattern['upper_intercept'] + pattern['upper_slope'] * (x - flag_start) for x in x_range]
    lower_y = [pattern['lower_intercept'] + pattern['lower_slope'] * (x - flag_start) for x in x_range]

    ax.plot(x_range, upper_y, 'r-', linewidth=2, alpha=0.7)
    ax.plot(x_range, lower_y, 'r-', linewidth=2, alpha=0.7)

    # Ausbruchspunkt
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

        # Position für Stärke-Anzeige (neben dem Fahnenmast)
        text_pos_x = pole_end
        text_pos_y = df['high'].iloc[pole_end] * 0.95

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_bearish_flag(ax, df, pattern):
    """
    Zeichnet ein bearisches Flaggen-Muster auf die Achse
    """
    # Fahnenmast zeichnen
    pole_start = pattern['pole_start']
    pole_end = pattern['pole_end']
    ax.plot([pole_start, pole_end],
            [df['high'].iloc[pole_start], df['low'].iloc[pole_end]],
            'r-', linewidth=3, alpha=0.7)

    # Flaggenkanal zeichnen
    flag_start = pattern['flag_start']
    flag_end = pattern['flag_end']

    # Berechne die Flaggenkanallinien
    x_range = range(flag_start, flag_end + 1)
    upper_y = [pattern['upper_intercept'] + pattern['upper_slope'] * (x - flag_start) for x in x_range]
    lower_y = [pattern['lower_intercept'] + pattern['lower_slope'] * (x - flag_start) for x in x_range]

    ax.plot(x_range, upper_y, 'g-', linewidth=2, alpha=0.7)
    ax.plot(x_range, lower_y, 'g-', linewidth=2, alpha=0.7)

    # Ausbruchspunkt
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

        # Position für Stärke-Anzeige (neben dem Fahnenmast)
        text_pos_x = pole_end
        text_pos_y = df['low'].iloc[pole_end] * 1.05

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_bullish_pennant(ax, df, pattern):
    """
    Zeichnet ein bullisches Wimpel-Muster auf die Achse
    """
    # Fahnenmast zeichnen
    pole_start = pattern['pole_start']
    pole_end = pattern['pole_end']
    ax.plot([pole_start, pole_end],
            [df['low'].iloc[pole_start], df['high'].iloc[pole_end]],
            'g-', linewidth=3, alpha=0.7)

    # Wimpel zeichnen (konvergierende Linien)
    pennant_start = pattern['pennant_start']
    pennant_end = pattern['pennant_end']

    # Berechne die Wimpellinien
    x_range = range(pennant_start, pennant_end + 1)
    upper_y = [pattern['upper_intercept'] + pattern['upper_slope'] * (x - pennant_start) for x in x_range]
    lower_y = [pattern['lower_intercept'] + pattern['lower_slope'] * (x - pennant_start) for x in x_range]

    ax.plot(x_range, upper_y, 'r-', linewidth=2, alpha=0.7)
    ax.plot(x_range, lower_y, 'g-', linewidth=2, alpha=0.7)

    # Ausbruchspunkt
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

        # Position für Stärke-Anzeige (in der Mitte des Wimpels)
        text_pos_x = (pennant_start + pennant_end) // 2
        mid_y = (pattern['upper_intercept'] + pattern['upper_slope'] * (text_pos_x - pennant_start) +
                 pattern['lower_intercept'] + pattern['lower_slope'] * (text_pos_x - pennant_start)) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, mid_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_bearish_pennant(ax, df, pattern):
    """
    Zeichnet ein bearisches Wimpel-Muster auf die Achse
    """
    # Fahnenmast zeichnen
    pole_start = pattern['pole_start']
    pole_end = pattern['pole_end']
    ax.plot([pole_start, pole_end],
            [df['high'].iloc[pole_start], df['low'].iloc[pole_end]],
            'r-', linewidth=3, alpha=0.7)

    # Wimpel zeichnen (konvergierende Linien)
    pennant_start = pattern['pennant_start']
    pennant_end = pattern['pennant_end']

    # Berechne die Wimpellinien
    x_range = range(pennant_start, pennant_end + 1)
    upper_y = [pattern['upper_intercept'] + pattern['upper_slope'] * (x - pennant_start) for x in x_range]
    lower_y = [pattern['lower_intercept'] + pattern['lower_slope'] * (x - pennant_start) for x in x_range]

    ax.plot(x_range, upper_y, 'r-', linewidth=2, alpha=0.7)
    ax.plot(x_range, lower_y, 'g-', linewidth=2, alpha=0.7)

    # Ausbruchspunkt
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

        # Position für Stärke-Anzeige (in der Mitte des Wimpels)
        text_pos_x = (pennant_start + pennant_end) // 2
        mid_y = (pattern['upper_intercept'] + pattern['upper_slope'] * (text_pos_x - pennant_start) +
                 pattern['lower_intercept'] + pattern['lower_slope'] * (text_pos_x - pennant_start)) / 2

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, mid_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def render_pattern(ax, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "bullish_flag":
        render_bullish_flag(ax, df, pattern)
    elif pattern_type == "bearish_flag":
        render_bearish_flag(ax, df, pattern)
    elif pattern_type == "bullish_pennant":
        render_bullish_pennant(ax, df, pattern)
    elif pattern_type == "bearish_pennant":
        render_bearish_pennant(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Flags: {pattern_type}")