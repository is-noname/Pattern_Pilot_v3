import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS
import plotly.graph_objects as go


SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen

def detect_double_bottom(df, config=None, timeframe="1d"):
    """
    Erkennt Double-Bottom-Muster im DataFrame.
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("double_bottom", PATTERN_CONFIGS.get("double_bottom", {}), timeframe)

    tolerance = config.get("tolerance", 0.03)
    lookback_periods = config.get("lookback_periods", 5)
    min_pattern_bars = config.get("min_pattern_bars", 5)

    if len(df) < lookback_periods * 2 + min_pattern_bars:
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
    # Suche nach Double-Bottom-Formationen
    for i in range(len(bottoms) - 1):
        idx1 = bottoms[i]
        idx2 = bottoms[i + 1]

        # Prüfe Abstand
        if idx2 - idx1 < min_pattern_bars:
            continue

        # Prüfe Preisähnlichkeit
        price_diff = abs(lows[idx1] - lows[idx2]) / lows[idx1]
        if price_diff > tolerance:
            continue

        # Bestimme Nackenlinie (höchster Punkt zwischen den Tiefs)
        neckline_idx = np.argmax(df['high'].values[idx1:idx2 + 1]) + idx1
        neckline = df['high'].values[neckline_idx]

        # Prüfe Durchbruch
        confirmed = False
        breakout_idx = None

        for j in range(idx2 + 1, min(len(df), idx2 + 20)):  # Suche in den nächsten 20 Kerzen
            if df['close'].values[j] > neckline:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen, wenn bestätigt oder auch unbestätigte anzeigen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Berechne Kursziel: Nackenlinie + Höhe des Musters
                pattern_height = neckline - min(lows[idx1], lows[idx2])
                target = neckline + pattern_height

            patterns.append({
                "type": "double_bottom",
                "P1": idx1,
                "P2": idx2,
                "neckline_idx": neckline_idx,
                "neckline": neckline,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": min(lows[idx1], lows[idx2]) * 0.98  # 2% unter dem tiefsten Punkt
            })

    return patterns


def render_double_bottom(ax, df, pattern):
    """
    Zeichnet ein Double Bottom Muster auf die Achse
    """
    # Zeichne Unterstützungspunkte
    ax.scatter(pattern['P1'], df['low'].iloc[pattern['P1']], color='lime', s=100, marker='o')
    ax.scatter(pattern['P2'], df['low'].iloc[pattern['P2']], color='lime', s=100, marker='o')

    # Nackenlinie
    ax.axhline(y=pattern['neckline'], color='r', linestyle='--', alpha=0.7,
               xmin=pattern['P1'] / len(df), xmax=pattern['P2'] / len(df))

    # Durchbruch (wenn bestätigt)
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                  color='lime', s=80, marker='^')

    # Optional: Kursziel anzeigen
    if pattern['confirmed'] and pattern['target'] is not None:
        # Projektion des Kursziels visualisieren
        target_y = pattern['target']
        breakout_x = pattern['breakout_idx']
        # Gepunktete Linie zum Kursziel
        ax.axhline(y=target_y, color='lime', linestyle=':', alpha=0.5,
                   xmin=breakout_x / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige
        text_pos_x = (pattern['P1'] + pattern['P2']) // 2
        text_pos_y = df['high'].iloc[
                         pattern['P1'] if df['high'].iloc[pattern['P1']] > df['high'].iloc[pattern['P2']] else pattern[
                             'P2']] * 1.02

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='red', alpha=0.3))


def detect_double_top(df, config=None, timeframe="1d"):
    """
    Erkennt Double-Top-Muster im DataFrame.
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("double_top", PATTERN_CONFIGS.get("double_top", {}), timeframe)

    tolerance = config.get("tolerance", 0.03)
    lookback_periods = config.get("lookback_periods", 5)
    min_pattern_bars = config.get("min_pattern_bars", 5)

    if len(df) < lookback_periods * 2 + min_pattern_bars:
        return []

    highs = df['high'].values
    tops = []

    # Finde lokale Hochs
    for i in range(lookback_periods, len(highs) - lookback_periods):
        prev = np.max(highs[i - lookback_periods:i])
        next_ = np.max(highs[i + 1:i + lookback_periods + 1])
        if highs[i] > prev and highs[i] > next_:
            tops.append(i)

    patterns = []
    # Suche nach Double-Top-Formationen
    for i in range(len(tops) - 1):
        idx1 = tops[i]
        idx2 = tops[i + 1]

        # Prüfe Abstand
        if idx2 - idx1 < min_pattern_bars:
            continue

        # Prüfe Preisähnlichkeit
        price_diff = abs(highs[idx1] - highs[idx2]) / highs[idx1]
        if price_diff > tolerance:
            continue

        # Bestimme Nackenlinie (tiefster Punkt zwischen den Hochs)
        neckline_idx = np.argmin(df['low'].values[idx1:idx2 + 1]) + idx1
        neckline = df['low'].values[neckline_idx]

        # Prüfe Durchbruch
        confirmed = False
        breakout_idx = None

        for j in range(idx2 + 1, min(len(df), idx2 + 20)):
            if df['close'].values[j] < neckline:
                confirmed = True
                breakout_idx = j
                break

        # Muster hinzufügen
        if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
            target = None
            if confirmed:
                # Kursziel: Nackenlinie - Höhe des Musters
                pattern_height = max(highs[idx1], highs[idx2]) - neckline
                target = neckline - pattern_height

            patterns.append({
                "type": "double_top",
                "P1": idx1,
                "P2": idx2,
                "neckline_idx": neckline_idx,
                "neckline": neckline,
                "confirmed": confirmed,
                "breakout_idx": breakout_idx,
                "target": target,
                "stop_loss": max(highs[idx1], highs[idx2]) * 1.02  # 2% über dem höchsten Punkt
            })


    return patterns


def render_double_top(ax, df, pattern):
    """
    Zeichnet ein Double Top Muster auf die Achse
    """
    # Zeichne Widerstandspunkte
    ax.scatter(pattern['P1'], df['high'].iloc[pattern['P1']], color='red', s=100, marker='o')
    ax.scatter(pattern['P2'], df['high'].iloc[pattern['P2']], color='red', s=100, marker='o')

    # Nackenlinie
    ax.axhline(y=pattern['neckline'], color='lime', linestyle='--', alpha=0.7,
              xmin=pattern['P1'] / len(df), xmax=pattern['P2'] / len(df))

    # Durchbruch (wenn bestätigt)
    if pattern['confirmed'] and pattern['breakout_idx'] is not None:
        ax.scatter(pattern['breakout_idx'], df['close'].iloc[pattern['breakout_idx']],
                  color='white', s=80, marker='v')
    
    # Optional: Kursziel anzeigen
    if pattern['confirmed'] and pattern['target'] is not None:
        # Projektion des Kursziels visualisieren
        target_y = pattern['target']
        breakout_x = pattern['breakout_idx']
        # Gepunktete Linie zum Kursziel
        ax.axhline(y=target_y, color='red', linestyle=':', alpha=0.5,
                   xmin=breakout_x / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige
        text_pos_x = (pattern['P1'] + pattern['P2']) // 2
        text_pos_y = df['high'].iloc[
                         pattern['P1'] if df['high'].iloc[pattern['P1']] > df['high'].iloc[pattern['P2']] else pattern[
                             'P2']] * 1.05

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

    if pattern_type == "double_bottom":
        render_double_bottom(ax, df, pattern)
    elif pattern_type == "double_top":
        render_double_top(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ: {pattern_type}")


# ================================================================================
# 🔹 RENDER FÜR PLOTLY CHARTS
# ================================================================================

def render_double_bottom_plotly(fig, df, pattern):
    """
    Plotly Version des Double Bottom Pattern Renderers

    Args:
        fig: Plotly Figure Objekt
        df: DataFrame mit OHLCV Daten
        pattern: Pattern Dictionary mit P1, P2, neckline, etc.
    """

    # =============================================================
    # 🔧 FIX: Index-Typ-Detection
    # =============================================================

    # Automatische X-Koordinaten je nach Index-Typ
    if isinstance(df.index, pd.RangeIndex):
        # RangeIndex: Nutze direkte Index-Zahlen
        x_coords = [pattern['P1'], pattern['P2']]
    else:
        # DatetimeIndex: Nutze df.index[position]
        x_coords = [df.index[pattern['P1']], df.index[pattern['P2']]]

    print(f"🔧 Using x_coords: {x_coords}")
    # =============================================================

    # ✅ Support Points (P1, P2) als grüne Marker
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=[df['low'].iloc[pattern['P1']], df['low'].iloc[pattern['P2']]],
        mode='markers',
        marker=dict(
            color='lime',
            size=12,
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        name='Double Bottom Support',
        showlegend=False,
        hovertemplate="<b>Support Point</b><br>" +
                      "Price: $%{y:.4f}<br>" +
                      "Index: %{x}<extra></extra>"
    ))

    # ✅ Neckline als gestrichelte horizontale Linie
    fig.add_shape(
        type="line",
        x0=x_coords[0],
        x1=x_coords[1],
        y0=pattern['neckline'],
        y1=pattern['neckline'],
        line=dict(
            color="red",
            width=2,
            dash="dash"
        )
    )

    # ✅ Neckline Label
    fig.add_annotation(
        x=df.index[pattern['P2']],
        y=pattern['neckline'],
        text=f"Neckline: ${pattern['neckline']:.4f}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        bgcolor="rgba(255,0,0,0.8)",
        bordercolor="red",
        font=dict(color="white", size=10)
    )

    # ✅ Breakout Point (falls bestätigt)
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        fig.add_trace(go.Scatter(
            x=[df.index[pattern['breakout_idx']]],
            y=[df['close'].iloc[pattern['breakout_idx']]],
            mode='markers',
            marker=dict(
                color='lime',
                size=15,
                symbol='triangle-up',
                line=dict(width=2, color='white')
            ),
            name='Breakout',
            showlegend=False,
            hovertemplate="<b>Breakout Point</b><br>" +
                          "Price: $%{y:.4f}<br>" +
                          "Confirmed: Yes<extra></extra>"
        ))

        # ✅ Target Line (Kursziel)
        if pattern.get('target') is not None:
            fig.add_shape(
                type="line",
                x0=df.index[pattern['breakout_idx']],
                x1=df.index[-1],  # Bis zum Ende des Charts
                y0=pattern['target'],
                y1=pattern['target'],
                line=dict(
                    color="lime",
                    width=2,
                    dash="dot"
                )
            )

            # Target Label
            fig.add_annotation(
                x=df.index[-1],
                y=pattern['target'],
                text=f"Target: ${pattern['target']:.4f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="lime",
                bgcolor="rgba(0,255,0,0.8)",
                bordercolor="lime",
                font=dict(color="white", size=10)
            )

    # =============================================================
    # 🔍 DEBUG KOORDINATEN-PROBLEM
    # =============================================================
    print(f"🔍 DEBUG Pattern: {pattern}")
    print(f"🔍 df.index type: {type(df.index)}")
    print(f"🔍 df.index[:5]: {df.index[:5]}")
    print(f"🔍 P1={pattern['P1']}, P2={pattern['P2']}")
    print(f"🔍 df.index[P1]={df.index[pattern['P1']]}")
    print(f"🔍 df.index[P2]={df.index[pattern['P2']]}")
    # =============================================================


def render_double_top_plotly(fig, df, pattern):
    """Plotly Version des Double Top Pattern Renderers"""

    # ✅ Resistance Points (P1, P2) als rote Marker
    fig.add_trace(go.Scatter(
        x=[df.index[pattern['P1']], df.index[pattern['P2']]],
        y=[df['high'].iloc[pattern['P1']], df['high'].iloc[pattern['P2']]],
        mode='markers',
        marker=dict(
            color='red',
            size=12,
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        name='Double Top Resistance',
        showlegend=False,
        hovertemplate="<b>Resistance Point</b><br>" +
                      "Price: $%{y:.4f}<br>" +
                      "Index: %{x}<extra></extra>"
    ))

    # ✅ Neckline als gestrichelte horizontale Linie
    fig.add_shape(
        type="line",
        x0=df.index[pattern['P1']],
        x1=df.index[pattern['P2']],
        y0=pattern['neckline'],
        y1=pattern['neckline'],
        line=dict(
            color="lime",
            width=2,
            dash="dash"
        )
    )

    # ✅ Breakout Point (falls bestätigt)
    if pattern.get('confirmed') and pattern.get('breakout_idx') is not None:
        fig.add_trace(go.Scatter(
            x=[df.index[pattern['breakout_idx']]],
            y=[df['close'].iloc[pattern['breakout_idx']]],
            mode='markers',
            marker=dict(
                color='red',
                size=15,
                symbol='triangle-down',
                line=dict(width=2, color='white')
            ),
            name='Breakdown',
            showlegend=False,
            hovertemplate="<b>Breakdown Point</b><br>" +
                          "Price: $%{y:.4f}<br>" +
                          "Confirmed: Yes<extra></extra>"
        ))


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", "unknown")

    if pattern_type == "double_bottom":
        render_double_bottom_plotly(fig, df, pattern)
    elif pattern_type == "double_top":
        render_double_top_plotly(fig, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Double-Patterns (Plotly): {pattern_type}")

# ================================================================================
# 🎯 USAGE EXAMPLES
# ================================================================================

"""
# Interactive Test (matplotlib):
patterns = detect_double_bottom(df)
for pattern in patterns:
    render_pattern(ax, df, pattern)  # Automatisch double_bottom

# App.py (plotly):
patterns = detect_double_bottom(df)
for pattern in patterns:
    render_pattern_plotly(fig, df, pattern)  # Automatisch double_bottom
"""