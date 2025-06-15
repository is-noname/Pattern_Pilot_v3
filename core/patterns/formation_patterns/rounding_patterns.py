import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT ROUNDING PATTERNS
# ==============================================================================
def detect_rounding_bottom(df, config=None, timeframe="1d"):
    """
    Erkennt Rounding Bottom (Cup) Muster (bullishes Umkehrmuster)

    Eigenschaften:
    - Allmähliche, bogenförmige Umkehr des Abwärtstrends
    - Schalenartige Form (U-förmig, nicht V-förmig)
    - Typischerweise lange Ausbildungszeit
    - Durchbruch über den Widerstand bestätigt das Muster
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("rounding_bottom", PATTERN_CONFIGS.get("rounding_bottom", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 15)  # Längere Periode für Rundungsmuster
    max_pattern_bars = config.get("max_pattern_bars", 100)
    smoothness = config.get("smoothness", 0.8)  # Wie "glatt" die Rundung sein muss (0-1)
    symmetry = config.get("symmetry", 0.7)  # Wie symmetrisch die Rundung sein muss (0-1)
    depth = config.get("depth", 0.1)  # Mindesttiefe der Rundung als Prozentsatz

    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Für verschiedene Muster-Startpunkte
    step_size = max(1, min(20, len(df) // 10))  # Reduziert die Anzahl der zu prüfenden Startpunkte
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length

            if end_idx >= len(df):
                continue

            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            prices = segment['close'].values

            # Die Rounding-Bottom-Formation muss eine allmähliche Rundung zeigen
            # Wir teilen das Segment in mehrere Teile und prüfen auf die runde Form

            # Für eine Rundung sollten die Preise zunächst fallen, dann flach sein und dann steigen
            n = len(prices)
            if n < min_pattern_bars:
                continue

            # Teile in Drittel für Analyse
            first_third = prices[:n // 3]
            middle_third = prices[n // 3:2 * n // 3]
            last_third = prices[2 * n // 3:]

            # Für ein Rounding Bottom: erste Drittel abfallend, letzte Drittel steigend
            is_first_declining = np.corrcoef(range(len(first_third)), first_third)[0, 1] < -0.3
            is_last_rising = np.corrcoef(range(len(last_third)), last_third)[0, 1] > 0.3

            if not (is_first_declining and is_last_rising):
                continue

            # Berechne die Tiefe des Musters
            start_price = prices[0]
            end_price = prices[-1]
            lowest_price = np.min(prices)

            pattern_depth = (max(start_price, end_price) - lowest_price) / max(start_price, end_price)

            if pattern_depth < depth:
                continue

            # Finde den Tiefpunkt - sollte etwa in der Mitte sein für gute Symmetrie
            lowest_idx = np.argmin(prices)
            middle_idx = n // 2

            # Symmetrie prüfen
            symmetry_score = 1.0 - abs(lowest_idx - middle_idx) / (n / 2)

            if symmetry_score < symmetry:
                continue

            # Ausbruch über den Widerstand suchen (Widerstand = Startpreis)
            resistance_level = start_price

            # Suche nach Breakout
            confirmed = False
            breakout_idx = None

            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                if df['close'].iloc[j] > resistance_level * 1.02:  # 2% Breakout
                    confirmed = True
                    breakout_idx = j
                    break

            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                target = None

                if confirmed:
                    # Kursziel: Ausbruchspunkt + Tiefe des Musters
                    target = df['close'].iloc[breakout_idx] + pattern_depth * resistance_level

                patterns.append({
                    "type": "rounding_bottom",
                    "start_idx": i,
                    "end_idx": end_idx,
                    "lowest_idx": i + lowest_idx,
                    "resistance_level": resistance_level,
                    "depth": pattern_depth,
                    "symmetry": symmetry_score,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target,
                    "stop_loss": lowest_price * 0.98  # 2% unter dem tiefsten Punkt
                })

    # Begrenze die Anzahl der zurückgegebenen Muster auf die besten
    if patterns:
        # Sortiere nach Tiefe und Symmetrie
        patterns.sort(key=lambda x: (x["depth"] * x["symmetry"]), reverse=True)
        return patterns[:3]  # Gib maximal 3 Ergebnisse zurück

    return patterns


def detect_rounding_top(df, config=None, timeframe="1d"):
    """
    Erkennt Rounding Top (Dome) Muster (bearishes Umkehrmuster)

    Eigenschaften:
    - Allmähliche, gewölbte Umkehr des Aufwärtstrends
    - Bogenförmige Form nach oben (umgekehrtes U)
    - Typischerweise lange Ausbildungszeit
    - Durchbruch unter die Unterstützung bestätigt das Muster
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("rounding_top", PATTERN_CONFIGS.get("rounding_top", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 15)  # Längere Periode für Rundungsmuster
    max_pattern_bars = config.get("max_pattern_bars", 100)
    smoothness = config.get("smoothness", 0.8)  # Wie "glatt" die Rundung sein muss (0-1)
    symmetry = config.get("symmetry", 0.7)  # Wie symmetrisch die Rundung sein muss (0-1)
    height = config.get("height", 0.1)  # Mindesthöhe der Rundung als Prozentsatz

    if len(df) < min_pattern_bars:
        return []  # Nicht genug Daten

    patterns = []

    # Für verschiedene Muster-Startpunkte
    step_size = max(1, min(20, len(df) // 10))  # Reduziert die Anzahl der zu prüfenden Startpunkte
    for i in range(0, len(df) - min_pattern_bars, step_size):
        for pattern_length in range(min_pattern_bars, min(max_pattern_bars, len(df) - i)):
            end_idx = i + pattern_length

            if end_idx >= len(df):
                continue

            # Segment ausschneiden
            segment = df.iloc[i:end_idx + 1].copy()
            prices = segment['close'].values

            # Die Rounding-Top-Formation muss eine allmähliche Rundung nach oben zeigen

            # Für eine Rundung sollten die Preise zunächst steigen, dann flach sein und dann fallen
            n = len(prices)
            if n < min_pattern_bars:
                continue

            # Teile in Drittel für Analyse
            first_third = prices[:n // 3]
            middle_third = prices[n // 3:2 * n // 3]
            last_third = prices[2 * n // 3:]

            # Für ein Rounding Top: erste Drittel steigend, letzte Drittel fallend
            is_first_rising = np.corrcoef(range(len(first_third)), first_third)[0, 1] > 0.3
            is_last_declining = np.corrcoef(range(len(last_third)), last_third)[0, 1] < -0.3

            if not (is_first_rising and is_last_declining):
                continue

            # Berechne die Höhe des Musters
            start_price = prices[0]
            end_price = prices[-1]
            highest_price = np.max(prices)

            pattern_height = (highest_price - min(start_price, end_price)) / min(start_price, end_price)

            if pattern_height < height:
                continue

            # Finde den Höchstpunkt - sollte etwa in der Mitte sein für gute Symmetrie
            highest_idx = np.argmax(prices)
            middle_idx = n // 2

            # Symmetrie prüfen
            symmetry_score = 1.0 - abs(highest_idx - middle_idx) / (n / 2)

            if symmetry_score < symmetry:
                continue

            # Ausbruch unter die Unterstützung suchen (Unterstützung = Startpreis)
            support_level = start_price

            # Suche nach Breakout
            confirmed = False
            breakout_idx = None

            for j in range(end_idx + 1, min(len(df), end_idx + 30)):
                if df['close'].iloc[j] < support_level * 0.98:  # 2% Breakout nach unten
                    confirmed = True
                    breakout_idx = j
                    break

            # Muster hinzufügen
            if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                target = None

                if confirmed:
                    # Kursziel: Ausbruchspunkt - Höhe des Musters
                    target = df['close'].iloc[breakout_idx] - pattern_height * support_level

                patterns.append({
                    "type": "rounding_top",
                    "start_idx": i,
                    "end_idx": end_idx,
                    "highest_idx": i + highest_idx,
                    "support_level": support_level,
                    "height": pattern_height,
                    "symmetry": symmetry_score,
                    "confirmed": confirmed,
                    "breakout_idx": breakout_idx,
                    "target": target,
                    "stop_loss": highest_price * 1.02  # 2% über dem höchsten Punkt
                })

    # Begrenze die Anzahl der zurückgegebenen Muster auf die besten
    if patterns:
        # Sortiere nach Höhe und Symmetrie
        patterns.sort(key=lambda x: (x["height"] * x["symmetry"]), reverse=True)
        return patterns[:3]  # Gib maximal 3 Ergebnisse zurück

    return patterns


# ==============================================================================
#                      RENDER ROUNDING PATTERNS IN MATPLOTLIB
# ==============================================================================

def render_rounding_bottom(ax, df, pattern):
    """
    Zeichnet ein Rounding Bottom Pattern mit einer glatten Kurve
    """
    # Hauptpunkte extrahieren
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']
    lowest_idx = pattern['lowest_idx']

    # Preise an den Hauptpunkten
    start_price = df['close'].iloc[start_idx]
    end_price = df['close'].iloc[end_idx]
    lowest_price = df['close'].iloc[lowest_idx]

    # Glatte Kurve mit vielen Punkten erzeugen
    import numpy as np
    from scipy import interpolate

    # Nur 3 Kontrollpunkte für die Kurve (Start, Tief, Ende)
    x_points = [start_idx, lowest_idx, end_idx]
    y_points = [start_price, lowest_price, end_price]

    # Erzeugt eine glatte Kurve durch diese Punkte
    x_smooth = np.linspace(start_idx, end_idx, 100)
    spline = interpolate.make_interp_spline(x_points, y_points, k=2)  # k=2 für quadratische Spline
    y_smooth = spline(x_smooth)

    # Zeichne die glatte Kurve
    ax.plot(x_smooth, y_smooth, color='lime', linewidth=2, alpha=0.7)

    # Markiere den tiefsten Punkt
    ax.scatter(lowest_idx, lowest_price, color='lime', s=80, marker='o')

    # Widerstandslinie zeichnen
    if 'resistance_level' in pattern:
        resistance_level = pattern['resistance_level']
        ax.axhline(y=resistance_level, color='r', linestyle='--', alpha=0.7,
                   xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Durchbruch und Kursziel anzeigen
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']
        ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                   color='lime', s=80, marker='^')

        if pattern.get('target') is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color='lime', linestyle=':', alpha=0.5,
                       xmin=breakout_idx / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (nahe dem tiefsten Punkt)
        text_pos_x = lowest_idx
        text_pos_y = lowest_price * 0.95

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_rounding_top(ax, df, pattern):
    """
    Zeichnet ein Rounding Top Pattern mit einfachem Bogen
    """
    # Hauptpunkte extrahieren
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']
    highest_idx = pattern['highest_idx']

    # Preise an den Hauptpunkten
    start_price = df['close'].iloc[start_idx]
    end_price = df['close'].iloc[end_idx]
    highest_price = df['high'].iloc[highest_idx]

    # Einfachen Kreisbogen zeichnen
    from matplotlib.patches import Arc
    import numpy as np

    # Berechne Mittelpunkt und Radius für den Bogen
    width = end_idx - start_idx
    height = highest_price - min(start_price, end_price)
    center_x = (start_idx + end_idx) / 2
    center_y = min(start_price, end_price)

    # Winkel berechnen (in Grad)
    theta1 = 0 if start_price <= end_price else 180
    theta2 = 180 if start_price <= end_price else 0

    # Bogen zeichnen
    arc = Arc((center_x, center_y + height / 2), width, height,
              theta1=0, theta2=180,  # Feste Werte für eine ∩-Form
              lw=2, color='red', alpha=0.7)
    ax.add_patch(arc)

    # Markiere den höchsten Punkt
    ax.scatter(highest_idx, highest_price, color='red', s=80, marker='o')

    # Unterstützungslinie zeichnen
    if 'support_level' in pattern:
        support_level = pattern['support_level']
        ax.axhline(y=support_level, color='lime', linestyle='--', alpha=0.7,
                   xmin=start_idx / len(df), xmax=end_idx / len(df))

    # Durchbruch und Kursziel anzeigen
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']
        ax.scatter(breakout_idx, df['close'].iloc[breakout_idx],
                   color='red', s=80, marker='v')

        if pattern.get('target') is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                       xmin=breakout_idx / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (nahe dem höchsten Punkt)
        text_pos_x = highest_idx
        text_pos_y = highest_price * 1.05

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

    if pattern_type == "rounding_bottom":
        render_rounding_bottom(ax, df, pattern)
    elif pattern_type == "rounding_top":
        render_rounding_top(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Rounding-Patterns: {pattern_type}")

# ==============================================================================
#                      RENDER ROUNDING PATTERNS IN PLOTLY
# ==============================================================================

# Pattern-spezifische Plotly Renderer definieren...
def render_rounding_bottom_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass

# Pattern-spezifische Plotly Renderer definieren...
def render_rounding_top_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "rounding_bottom":
        render_rounding_bottom_plotly(fig, df, pattern)
    elif pattern_type == "rounding_top":
        render_rounding_top_plotly(fig, df, pattern)
    # ... weitere Pattern-Typen in dieser Datei ...
    else:
        print(f"Unbekannter Pattern-Typ für DATEI_NAME (Plotly): {pattern_type}")