import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


# ==============================================================================
#                      DETECT V / CUP PATTERNS
# ==============================================================================
def detect_v_pattern(df, config=None, timeframe="1d"):
    """
    Erkennt V-Muster (Spike) - eine scharfe, schnelle Umkehr
    
    Eigenschaften:
    - Scharfe, V-förmige Umkehr ohne Konsolidierung
    - Starker Momentum-Wechsel
    - Typisch für Panik-Verkäufe oder -Käufe
    - Steiler Trend gefolgt von schneller Umkehr
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("v_pattern", PATTERN_CONFIGS.get("v_pattern", {}), timeframe)

    min_pattern_bars = config.get("min_pattern_bars", 5)
    max_pattern_bars = config.get("max_pattern_bars", 30)
    min_angle = config.get("min_angle", 45)  # Mindestwinkel für jeden Schenkel (in Grad)
    min_depth = config.get("min_depth", 0.05)  # Mindesttief/höhe als Prozent
    
    if len(df) < min_pattern_bars * 2:
        return []  # Nicht genug Daten
    
    patterns = []
    
    # V-Muster kann bearish (∧) oder bullish (V) sein
    # Zunächst suchen wir nach potenziellen Umkehrpunkten
    
    # Für bearish V (∧)
    for i in range(min_pattern_bars, len(df) - min_pattern_bars):
        # Prüfe, ob wir einen lokalen Hochpunkt haben
        if not (df['high'].iloc[i] > df['high'].iloc[i-1:i].max() and 
                df['high'].iloc[i] > df['high'].iloc[i+1:i+min_pattern_bars].max()):
            continue
        
        # Berechne linke Seite der V-Formation
        left_prices = df['close'].iloc[i-min_pattern_bars:i+1]
        left_idx = np.arange(len(left_prices))
        
        # Berechne rechte Seite der V-Formation
        right_prices = df['close'].iloc[i:i+min_pattern_bars+1]
        right_idx = np.arange(len(right_prices))
        
        # Berechne die Steigungen beider Seiten
        try:
            left_slope, _ = np.polyfit(left_idx, left_prices, 1)
            right_slope, _ = np.polyfit(right_idx, right_prices, 1)
        except:
            continue  # Bei Fehlern überspringen
        
        # Konvertiere Steigung in Winkel (in Grad)
        left_angle = np.abs(np.degrees(np.arctan(left_slope)))
        right_angle = np.abs(np.degrees(np.arctan(right_slope)))
        
        # Prüfe Winkel und Richtung:
        # Für bearish V: linke Seite steigend, rechte Seite fallend
        if not (left_angle >= min_angle and right_angle >= min_angle and left_slope > 0 and right_slope < 0):
            continue
        
        # Berechne die Tiefe des Musters
        pivot_price = df['high'].iloc[i]
        left_start = df['close'].iloc[i-min_pattern_bars]
        right_end = df['close'].iloc[i+min_pattern_bars]
        
        pattern_height = (pivot_price - min(left_start, right_end)) / min(left_start, right_end)
        
        if pattern_height < min_depth:
            continue
        
        # V-Muster hinzufügen
        patterns.append({
            "type": "v_pattern",
            "subtype": "bearish",  # ∧ Form
            "pivot_idx": i,
            "start_idx": i - min_pattern_bars,
            "end_idx": i + min_pattern_bars,
            "left_angle": left_angle,
            "right_angle": right_angle,
            "height": pattern_height,
            "pivot_price": pivot_price,
            # V-Muster hat keinen typischen Breakout, da die Umkehr bereits stattgefunden hat
            "target": None  # Kein spezifisches Kursziel
        })
    
    # Für bullish V (V)
    for i in range(min_pattern_bars, len(df) - min_pattern_bars):
        # Prüfe, ob wir einen lokalen Tiefpunkt haben
        if not (df['low'].iloc[i] < df['low'].iloc[i-min_pattern_bars:i].min() and 
                df['low'].iloc[i] < df['low'].iloc[i+1:i+min_pattern_bars].min()):
            continue
        
        # Berechne linke Seite der V-Formation
        left_prices = df['close'].iloc[i-min_pattern_bars:i+1]
        left_idx = np.arange(len(left_prices))
        
        # Berechne rechte Seite der V-Formation
        right_prices = df['close'].iloc[i:i+min_pattern_bars+1]
        right_idx = np.arange(len(right_prices))
        
        # Berechne die Steigungen beider Seiten
        try:
            left_slope, _ = np.polyfit(left_idx, left_prices, 1)
            right_slope, _ = np.polyfit(right_idx, right_prices, 1)
        except:
            continue  # Bei Fehlern überspringen
        
        # Konvertiere Steigung in Winkel (in Grad)
        left_angle = np.abs(np.degrees(np.arctan(left_slope)))
        right_angle = np.abs(np.degrees(np.arctan(right_slope)))
        
        # Prüfe Winkel und Richtung:
        # Für bullish V: linke Seite fallend, rechte Seite steigend
        if not (left_angle >= min_angle and right_angle >= min_angle and left_slope < 0 and right_slope > 0):
            continue
        
        # Berechne die Tiefe des Musters
        pivot_price = df['low'].iloc[i]
        left_start = df['close'].iloc[i-min_pattern_bars]
        right_end = df['close'].iloc[i+min_pattern_bars]
        
        pattern_depth = (max(left_start, right_end) - pivot_price) / max(left_start, right_end)
        
        if pattern_depth < min_depth:
            continue
        
        # V-Muster hinzufügen
        patterns.append({
            "type": "v_pattern",
            "subtype": "bullish",  # V Form
            "pivot_idx": i,
            "start_idx": i - min_pattern_bars,
            "end_idx": i + min_pattern_bars,
            "left_angle": left_angle,
            "right_angle": right_angle,
            "depth": pattern_depth,
            "pivot_price": pivot_price,
            # V-Muster hat keinen typischen Breakout, da die Umkehr bereits stattgefunden hat
            "target": None  # Kein spezifisches Kursziel
        })
    
    # Sortiere Muster nach Tiefe/Höhe und Winkel
    patterns.sort(key=lambda x: (x.get("depth", 0) + x.get("height", 0)) * (x["left_angle"] + x["right_angle"]), 
                 reverse=True)
    
    # Begrenze Anzahl der Ergebnisse
    return patterns[:5]  # Maximal 5 V-Muster zurückgeben


def detect_cup_and_handle(df, config=None, timeframe="1d"):
    """
    Erkennt Cup-and-Handle-Muster (bullishes Fortsetzungsmuster)
    
    Eigenschaften:
    - U-förmige Cup-Formation (Rounding Bottom) gefolgt von einem kurzen Rücksetzer (Handle)
    - Handle sollte flacher sein als der Cup und nicht zu tief reichen
    - Ausbruch über den Widerstand am Cup-/Handle-Rand bestätigt das Muster
    """
    # Config laden
    if config is None:
        from core.patterns import get_pattern_config
        config = get_pattern_config("cup_and_handle", PATTERN_CONFIGS.get("cup_and_handle", {}), timeframe)
    
    min_cup_bars = config.get("min_cup_bars", 20)  # Cup sollte länger sein
    max_cup_bars = config.get("max_cup_bars", 100)
    min_handle_bars = config.get("min_handle_bars", 5)
    max_handle_bars = config.get("max_handle_bars", 20)
    handle_depth_ratio = config.get("handle_depth_ratio", 0.5)  # Handle sollte nicht tiefer als 50% des Cups sein
    
    if len(df) < min_cup_bars + min_handle_bars:
        return []  # Nicht genug Daten
    
    patterns = []
    
    # Zuerst suchen wir nach cup-ähnlichen Formationen (ähnlich wie bei rounding_bottom)
    step_size = max(1, min(20, len(df) // 20))  # Für Performance-Optimierung
    for i in range(0, len(df) - min_cup_bars - min_handle_bars, step_size):
        for cup_length in range(min_cup_bars, min(max_cup_bars, len(df) - i - min_handle_bars)):
            cup_end_idx = i + cup_length
            
            # Cup-Segment ausschneiden
            cup_segment = df.iloc[i:cup_end_idx + 1].copy()
            cup_prices = cup_segment['close'].values
            
            # Für einen Cup: Preise fallen, dann steigen (U-Form)
            n = len(cup_prices)
            if n < min_cup_bars:
                continue
            
            # Teile in Hälften
            first_half = cup_prices[:n//2]
            second_half = cup_prices[n//2:]
            
            # Cup-Form prüfen
            is_first_declining = np.corrcoef(range(len(first_half)), first_half)[0, 1] < -0.1
            is_second_rising = np.corrcoef(range(len(second_half)), second_half)[0, 1] > 0.1
            
            if not (is_first_declining and is_second_rising):
                continue
            
            # Cup-Tiefe prüfen
            cup_start_price = cup_prices[0]
            cup_end_price = cup_prices[-1]
            cup_bottom = np.min(cup_prices)
            
            cup_depth = (max(cup_start_price, cup_end_price) - cup_bottom) / max(cup_start_price, cup_end_price)
            
            if cup_depth < 0.1:  # Cup sollte mindestens 10% tief sein
                continue
            
            # Cup-Rand-Level (Widerstand)
            resistance_level = max(cup_start_price, cup_end_price)
            
            # Jetzt suchen wir nach dem Handle
            for handle_length in range(min_handle_bars, min(max_handle_bars, len(df) - cup_end_idx - 1)):
                handle_end_idx = cup_end_idx + handle_length
                
                if handle_end_idx >= len(df):
                    continue
                
                # Handle-Segment ausschneiden
                handle_segment = df.iloc[cup_end_idx:handle_end_idx + 1].copy()
                handle_prices = handle_segment['close'].values
                
                # Handle-Form prüfen: leichte Abwärtsbewegung (flacher als der Cup)
                handle_low = np.min(handle_prices)
                handle_depth = (cup_end_price - handle_low) / cup_end_price
                
                # Handle sollte flacher sein als der Cup und nicht zu tief reichen
                if handle_depth > cup_depth * handle_depth_ratio or handle_depth < 0.03:
                    continue
                
                # Handle sollte nicht unter das Cup-Tief fallen
                if handle_low < cup_bottom:
                    continue
                
                # Suche nach Ausbruch über den Widerstand
                confirmed = False
                breakout_idx = None
                
                for j in range(handle_end_idx + 1, min(len(df), handle_end_idx + 30)):
                    if df['close'].iloc[j] > resistance_level * 1.01:  # 1% Breakout
                        confirmed = True
                        breakout_idx = j
                        break
                
                # Muster hinzufügen
                if confirmed or not PATTERN_CONFIGS.get("only_confirmed", False):
                    target = None
                    
                    if confirmed:
                        # Kursziel: Ausbruchspunkt + Tiefe des Cups
                        target = df['close'].iloc[breakout_idx] + cup_depth * resistance_level
                    
                    patterns.append({
                        "type": "cup_and_handle",
                        "cup_start_idx": i,
                        "cup_end_idx": cup_end_idx,
                        "handle_end_idx": handle_end_idx,
                        "cup_depth": cup_depth,
                        "handle_depth": handle_depth,
                        "resistance_level": resistance_level,
                        "confirmed": confirmed,
                        "breakout_idx": breakout_idx,
                        "target": target,
                        "stop_loss": handle_low * 0.98  # 2% unter dem Handle-Tief
                    })
    
    # Sortiere nach Qualität
    if patterns:
        patterns.sort(key=lambda x: x["cup_depth"], reverse=True)
        return patterns[:3]  # Maximal 3 Ergebnisse
    
    return patterns


# ==============================================================================
#                      RENDER V / CUP PATTERNS IN MATPLOTLIB
# ==============================================================================
def render_v_pattern(ax, df, pattern):
    """
    Zeichnet ein V-Pattern auf die Achse
    """
    # Extrahiere die Hauptpunkte des Patterns
    pivot_idx = pattern['pivot_idx']
    start_idx = pattern['start_idx']
    end_idx = pattern['end_idx']

    # Färbung je nach Subtyp (bullish/bearish)
    color = 'lime' if pattern['subtype'] == 'bullish' else 'red'

    # Zeichne die V-Form durch Verbinden der drei Hauptpunkte
    x_points = [start_idx, pivot_idx, end_idx]
    y_points = [
        df['close'].iloc[start_idx],
        pattern.get('pivot_price') if 'pivot_price' in pattern else (
            df['low'].iloc[pivot_idx] if pattern['subtype'] == 'bullish' else df['high'].iloc[pivot_idx]
        ),
        df['close'].iloc[end_idx]
    ]

    # Zeichne die V-Form
    ax.plot(x_points, y_points, color=color, linewidth=2, alpha=0.7)

    # Markiere den Scheitelpunkt
    pivot_price = df['low'].iloc[pivot_idx] if pattern['subtype'] == 'bullish' else df['high'].iloc[pivot_idx]
    ax.scatter(pivot_idx, pivot_price, color=color, s=80, marker='o')

    # Markiere Winkel
    if 'left_angle' in pattern and 'right_angle' in pattern:
        # Winkeltext nahe beim Scheitelpunkt anzeigen
        angles_text = f"∠L:{pattern['left_angle']:.1f}° ∠R:{pattern['right_angle']:.1f}°"
        ax.annotate(angles_text, (pivot_idx, pivot_price),
                    xytext=(10, 10 if pattern['subtype'] == 'bullish' else -10),
                    textcoords='offset points', fontsize=8, alpha=0.7)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (abhängig vom Subtyp)
        text_pos_x = pivot_idx
        if pattern['subtype'] == 'bullish':
            text_pos_y = pivot_price * 0.95
            bg_color = 'green'
        else:
            text_pos_y = pivot_price * 1.05
            bg_color = 'red'

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor=bg_color, alpha=0.3))


def render_cup_and_handle(ax, df, pattern):
    """
    Zeichnet ein Cup-and-Handle Pattern auf die Achse
    """
    # Extrahiere die Hauptpunkte des Patterns
    cup_start_idx = pattern['cup_start_idx']
    cup_end_idx = pattern['cup_end_idx']
    handle_end_idx = pattern['handle_end_idx']

    # Cup zeichnen (U-Form)
    # Für eine schönere U-Form verwenden wir mehr Punkte und eine Spline-Kurve
    cup_segment = df.iloc[cup_start_idx:cup_end_idx + 1]
    cup_x = range(cup_start_idx, cup_end_idx + 1)
    cup_y = cup_segment['close'].values

    # Zeichne die Cup-Form
    ax.plot(cup_x, cup_y, color='lime', linewidth=2, alpha=0.7)

    # Handle zeichnen (kleinere Abwärtsbewegung)
    handle_segment = df.iloc[cup_end_idx:handle_end_idx + 1]
    handle_x = range(cup_end_idx, handle_end_idx + 1)
    handle_y = handle_segment['close'].values

    # Zeichne den Handle
    ax.plot(handle_x, handle_y, color='lime', linewidth=2, alpha=0.7)

    # Widerstandslinie zeichnen
    resistance_level = pattern['resistance_level']
    ax.axhline(y=resistance_level, color='r', linestyle='--', alpha=0.7,
               xmin=cup_start_idx / len(df), xmax=handle_end_idx / len(df))

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

        # Position für Stärke-Anzeige (im Cup)
        cup_mid_idx = (cup_start_idx + cup_end_idx) // 2
        cup_bottom_price = min(cup_segment['close'].values)
        text_pos_x = cup_mid_idx
        text_pos_y = cup_bottom_price * 0.95

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor='green', alpha=0.3))


def render_v_cup_pattern(ax, df, pattern):
    """
    Rendert ein V- oder Cup-Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "v_pattern":
        render_v_pattern(ax, df, pattern)
    elif pattern_type == "cup_and_handle":
        render_cup_and_handle(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für V/Cup: {pattern_type}")

# ==============================================================================
#                      RENDER V / CUP PATTERNS IN PLOTLY
# ==============================================================================

# Pattern-spezifische Plotly Renderer definieren...
def render_v_pattern_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass

# Pattern-spezifische Plotly Renderer definieren...
def render_cup_and_handle_plotly(fig, df, pattern):
    # ... Implementierung ...
    pass


def render_pattern_plotly(fig, df, pattern):
    """
    Rendert ein Pattern basierend auf seinem Typ (PLOTLY)
    """
    pattern_type = pattern.get("type", 'unknown')

    if pattern_type == "v_pattern":
        render_v_pattern_plotly(fig, df, pattern)
    elif pattern_type == "cup_and_handle":
        render_cup_and_handle_plotly(fig, df, pattern)
    # ... weitere Pattern-Typen in dieser Datei ...
    else:
        print(f"Unbekannter Pattern-Typ für DATEI_NAME (Plotly): {pattern_type}")
