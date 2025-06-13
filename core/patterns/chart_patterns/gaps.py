import pandas as pd
import numpy as np
from config.pattern_settings import PATTERN_CONFIGS

SHOW_STRENGTH_IN_CHART = False  # Diese Zeile hinzufügen


def _identify_gaps(df):
    """
    Identifiziert alle Gaps (Kurslücken) in den Preisdaten.
    Ein Gap entsteht, wenn zwischen dem Schlusskurs einer Periode und
    dem Eröffnungskurs der nächsten Periode eine Lücke besteht.
    
    Returns:
        List von Dictionaries mit Gap-Details
    """
    gaps = []
    
    if len(df) < 2:
        return gaps
        
    # Durchlaufe Daten und finde Gaps
    for i in range(1, len(df)):
        prev_close = df['close'].iloc[i-1]
        current_open = df['open'].iloc[i]
        current_close = df['close'].iloc[i]
        
        # Up Gap: Open über dem vorherigen Close
        if current_open > prev_close:
            gap_size = (current_open - prev_close) / prev_close  # Relative Größe
            
            # Nur signifikante Gaps (mindestens 0.5% der Höhe)
            if gap_size >= 0.005:
                gap = {
                    "idx": i,
                    "type": "up",
                    "size": gap_size,
                    "gap": current_open - prev_close,  # Absolute Größe
                    "filled": False,  # Initialisierung, wird später geprüft
                    "fill_idx": None
                }
                gaps.append(gap)
                
        # Down Gap: Open unter dem vorherigen Close
        elif current_open < prev_close:
            gap_size = (prev_close - current_open) / prev_close  # Relative Größe
            
            # Nur signifikante Gaps (mindestens 0.5% der Höhe)
            if gap_size >= 0.005:
                gap = {
                    "idx": i,
                    "type": "down",
                    "size": gap_size,
                    "gap": prev_close - current_open,  # Absolute Größe
                    "filled": False,  # Initialisierung, wird später geprüft
                    "fill_idx": None
                }
                gaps.append(gap)
    
    # Prüfe, ob und wann Gaps gefüllt wurden
    for gap in gaps:
        gap_idx = gap["idx"]
        
        if gap["type"] == "up":
            # Ein Up-Gap ist gefüllt, wenn der Preis später wieder unter/auf den vorherigen Close fällt
            prev_close = df['close'].iloc[gap_idx-1]
            
            for j in range(gap_idx+1, len(df)):
                if df['low'].iloc[j] <= prev_close:
                    gap["filled"] = True
                    gap["fill_idx"] = j
                    break
                    
        else:  # Down Gap
            # Ein Down-Gap ist gefüllt, wenn der Preis später wieder über/auf den vorherigen Close steigt
            prev_close = df['close'].iloc[gap_idx-1]
            
            for j in range(gap_idx+1, len(df)):
                if df['high'].iloc[j] >= prev_close:
                    gap["filled"] = True
                    gap["fill_idx"] = j
                    break
    
    return gaps


def _analyze_trend(df, start_idx, end_idx, window=10):
    """
    Analysiert den Trend im angegebenen Bereich.
    
    Args:
        df: DataFrame mit Preisdaten
        start_idx: Startindex für die Analyse
        end_idx: Endindex für die Analyse
        window: Fenstergröße für die Trendanalyse
        
    Returns:
        Dictionary mit Trendinformationen
    """
    if start_idx < 0:
        start_idx = 0
        
    if end_idx >= len(df):
        end_idx = len(df) - 1
        
    if end_idx - start_idx < window:
        window = max(2, end_idx - start_idx)
        
    # Berechne lineare Regression über den Bereich
    segment = df.iloc[start_idx:end_idx+1]
    x = np.arange(len(segment))
    y = segment['close'].values
    
    try:
        slope, intercept = np.polyfit(x, y, 1)
    except:
        # Fallback bei Fehler
        return {
            "direction": "sideways",
            "strength": 0.0
        }
    
    # Berechne Korrelationskoeffizient für Trendstärke
    correlation = np.corrcoef(x, y)[0, 1]
    trend_strength = abs(correlation)
    
    # Bestimme Trendrichtung
    if slope > 0 and correlation > 0.5:
        direction = "up"
    elif slope < 0 and correlation < -0.5:
        direction = "down"
    else:
        direction = "sideways"
        
    return {
        "direction": direction,
        "strength": trend_strength,
        "slope": slope
    }


def detect_breakaway_gap(df, config=None, timeframe="1d"):
    """
    Erkennt Breakaway Gaps - Ausbruchs-Gaps am Anfang eines neuen Trends
    
    Eigenschaften:
    - Tritt am Anfang eines neuen Trends auf
    - Oft nach Konsolidierungsphase oder an Musterausbrüchen
    - Hohe prognostische Bedeutung für die Trendrichtung
    - Meistens mit erhöhtem Volumen
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("breakaway_gap", PATTERN_CONFIGS.get("breakaway_gap", {}), timeframe)
        
    min_gap_size = config.get("min_gap_size", 0.01)  # Mindestgröße des Gaps (1%)
    pre_trend_window = config.get("pre_trend_window", 10)  # Fenster zur Analyse des vorherigen Trends
    post_trend_window = config.get("post_trend_window", 10)  # Fenster zur Analyse des folgenden Trends
    min_post_trend_strength = config.get("min_post_trend_strength", 0.6)  # Mindeststärke des neuen Trends
    
    if len(df) < max(pre_trend_window, post_trend_window) * 2:
        return []  # Nicht genug Daten
        
    # Identifiziere alle Gaps
    all_gaps = _identify_gaps(df)
    
    # Filtere nach Breakaway Gaps
    breakaway_gaps = []
    
    for gap in all_gaps:
        gap_idx = gap["idx"]
        
        # Prüfe Größe des Gaps
        if gap["size"] < min_gap_size:
            continue
            
        # Analysiere Trend vor dem Gap
        pre_trend = _analyze_trend(df, max(0, gap_idx - pre_trend_window), gap_idx - 1)
        
        # Analysiere Trend nach dem Gap
        if gap_idx + post_trend_window >= len(df):
            continue  # Nicht genug Daten nach dem Gap
            
        post_trend = _analyze_trend(df, gap_idx, min(len(df) - 1, gap_idx + post_trend_window))
        
        # Breakaway Gap: Signifikante Änderung der Trendrichtung oder Trendstärke
        trend_change = pre_trend["direction"] != post_trend["direction"]
        significant_acceleration = (post_trend["strength"] > min_post_trend_strength and 
                                   post_trend["strength"] > pre_trend["strength"] * 1.5)
        
        # Bei Up-Gap sollte ein Aufwärtstrend folgen, bei Down-Gap ein Abwärtstrend
        trend_alignment = ((gap["type"] == "up" and post_trend["direction"] == "up") or
                          (gap["type"] == "down" and post_trend["direction"] == "down"))
                          
        # Prüfe auf erhöhtes Volumen, falls verfügbar
        volume_confirms = True
        if 'volume' in df.columns:
            prev_avg_volume = df['volume'].iloc[max(0, gap_idx - 5):gap_idx].mean()
            gap_volume = df['volume'].iloc[gap_idx]
            volume_confirms = gap_volume > prev_avg_volume * 1.5
            
        # Breakaway Gap bestätigen
        if (trend_alignment and (trend_change or significant_acceleration)):
            target = None
            
            # Nur wenn ausreichend Daten für ein Kursziel
            if gap_idx + 20 < len(df):
                # Kursziel: Gap-Größe projiziert in Trendrichtung
                if gap["type"] == "up":
                    target = df['close'].iloc[gap_idx] + gap["gap"] * 2
                else:
                    target = df['close'].iloc[gap_idx] - gap["gap"] * 2
                    
            breakaway_gaps.append({
                "type": "breakaway_gap",
                "subtype": gap["type"],  # "up" oder "down"
                "idx": gap_idx,
                "size": gap["size"],
                "gap": gap["gap"],
                "pre_trend": pre_trend["direction"],
                "post_trend": post_trend["direction"],
                "volume_confirms": volume_confirms,
                "filled": gap["filled"],
                "fill_idx": gap["fill_idx"],
                "target": target
            })
            
    return breakaway_gaps


def detect_runaway_gap(df, config=None, timeframe="1d"):
    """
    Erkennt Runaway Gaps (Measuring Gaps) - Fortsetzungs-Gaps während eines starken Trends
    
    Eigenschaften:
    - Tritt während eines bereits starken, etablierten Trends auf
    - Signalisiert Fortsetzung und oft etwa die Hälfte der Gesamtbewegung
    - Häufig mit starkem Momentum und guter Volumenbestätigung
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("runaway_gap", PATTERN_CONFIGS.get("runaway_gap", {}), timeframe)
        
    min_gap_size = config.get("min_gap_size", 0.01)  # Mindestgröße des Gaps (1%)
    trend_window = config.get("trend_window", 15)  # Fenster zur Analyse des bestehenden Trends
    min_trend_strength = config.get("min_trend_strength", 0.7)  # Mindeststärke des bestehenden Trends
    
    if len(df) < trend_window * 2:
        return []  # Nicht genug Daten
        
    # Identifiziere alle Gaps
    all_gaps = _identify_gaps(df)
    
    # Filtere nach Runaway Gaps
    runaway_gaps = []
    
    for gap in all_gaps:
        gap_idx = gap["idx"]
        
        # Prüfe Größe des Gaps
        if gap["size"] < min_gap_size:
            continue
            
        # Für Runaway Gaps benötigen wir vor dem Gap Daten für den bestehenden Trend
        if gap_idx < trend_window:
            continue
            
        # Analysiere Trend vor dem Gap
        pre_trend = _analyze_trend(df, gap_idx - trend_window, gap_idx - 1)
        
        # Analysiere Trend nach dem Gap
        post_trend_window = min(trend_window, len(df) - gap_idx - 1)
        if post_trend_window < trend_window // 2:
            continue  # Nicht genug Daten nach dem Gap
            
        post_trend = _analyze_trend(df, gap_idx, gap_idx + post_trend_window)
        
        # Runaway Gap: Trendrichtung bleibt gleich, Gap in Trendrichtung
        trend_continuation = pre_trend["direction"] == post_trend["direction"]
        strong_trend = pre_trend["strength"] > min_trend_strength
        
        # Bei Up-Gap sollte ein Aufwärtstrend sein, bei Down-Gap ein Abwärtstrend
        trend_alignment = ((gap["type"] == "up" and pre_trend["direction"] == "up") or
                          (gap["type"] == "down" and pre_trend["direction"] == "down"))
                          
        # Prüfe auf angemessenes Volumen, falls verfügbar
        volume_confirms = True
        if 'volume' in df.columns:
            prev_avg_volume = df['volume'].iloc[max(0, gap_idx - 5):gap_idx].mean()
            gap_volume = df['volume'].iloc[gap_idx]
            volume_confirms = gap_volume > prev_avg_volume
        
        # Runaway Gap bestätigen
        if trend_continuation and strong_trend and trend_alignment:
            target = None
            
            # Berechne mögliches Kursziel
            if gap_idx + 20 < len(df):
                # Berechne Trendlänge vor dem Gap
                start_trend_idx = max(0, gap_idx - trend_window)
                trend_start_price = df['close'].iloc[start_trend_idx]
                gap_price = df['close'].iloc[gap_idx]
                
                pre_move = abs(gap_price - trend_start_price)
                
                # Kursziel: Oft ungefähr die gleiche Distanz vom Gap aus
                if gap["type"] == "up":
                    target = gap_price + pre_move
                else:
                    target = gap_price - pre_move
                    
            runaway_gaps.append({
                "type": "runaway_gap",
                "subtype": gap["type"],  # "up" oder "down"
                "idx": gap_idx,
                "size": gap["size"],
                "gap": gap["gap"],
                "trend_direction": pre_trend["direction"],
                "trend_strength": pre_trend["strength"],
                "volume_confirms": volume_confirms,
                "filled": gap["filled"],
                "fill_idx": gap["fill_idx"],
                "target": target
            })
            
    return runaway_gaps


def detect_exhaustion_gap(df, config=None, timeframe="1d"):
    """
    Erkennt Exhaustion Gaps - Erschöpfungs-Gaps am Ende eines Trends
    
    Eigenschaften:
    - Tritt am Ende eines bereits ausgedehnten Trends auf
    - Oft das letzte Gap in einer Gap-Serie
    - Häufig gefolgt von Trendumkehr
    - Wird typischerweise schnell gefüllt
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("exhaustion_gap", PATTERN_CONFIGS.get("exhaustion_gap", {}), timeframe)
        
    min_gap_size = config.get("min_gap_size", 0.01)  # Mindestgröße des Gaps (1%)
    trend_window = config.get("trend_window", 20)  # Fenster zur Analyse des bestehenden Trends
    post_reversal_window = config.get("post_reversal_window", 10)  # Fenster zur Analyse der Umkehr
    min_trend_duration = config.get("min_trend_duration", 15)  # Mindestdauer des vorherigen Trends
    max_fill_bars = config.get("max_fill_bars", 5)  # Max. Anzahl Kerzen bis zur Füllung des Gaps
    
    if len(df) < trend_window + post_reversal_window:
        return []  # Nicht genug Daten
        
    # Identifiziere alle Gaps
    all_gaps = _identify_gaps(df)
    
    # Filtere nach Exhaustion Gaps
    exhaustion_gaps = []
    
    for gap in all_gaps:
        gap_idx = gap["idx"]
        
        # Prüfe Größe des Gaps
        if gap["size"] < min_gap_size:
            continue
            
        # Für Exhaustion Gaps benötigen wir ausreichend Daten vor und nach dem Gap
        if gap_idx < min_trend_duration or gap_idx + post_reversal_window >= len(df):
            continue
            
        # Analysiere Trend vor dem Gap
        pre_trend = _analyze_trend(df, gap_idx - trend_window, gap_idx - 1)
        
        # Analysiere Trend nach dem Gap
        post_trend = _analyze_trend(df, gap_idx, min(len(df) - 1, gap_idx + post_reversal_window))
        
        # Exhaustion Gap: Trendumkehr nach dem Gap
        trend_reversal = ((pre_trend["direction"] == "up" and post_trend["direction"] == "down") or
                          (pre_trend["direction"] == "down" and post_trend["direction"] == "up"))
                          
        # Bei Up-Gap sollte ein Aufwärtstrend vor dem Gap sein, bei Down-Gap ein Abwärtstrend
        trend_alignment = ((gap["type"] == "up" and pre_trend["direction"] == "up") or
                          (gap["type"] == "down" and pre_trend["direction"] == "down"))
        
        # Das Gap sollte schnell gefüllt werden
        rapid_filling = gap["filled"] and (gap["fill_idx"] - gap_idx) <= max_fill_bars
        
        # Prüfe auf abnehmendes Volumen, falls verfügbar
        volume_declining = True
        if 'volume' in df.columns:
            prev_avg_volume = df['volume'].iloc[max(0, gap_idx - 5):gap_idx].mean()
            gap_volume = df['volume'].iloc[gap_idx]
            post_volume = df['volume'].iloc[gap_idx+1:min(len(df), gap_idx+5)].mean()
            volume_declining = post_volume < gap_volume and gap_volume < prev_avg_volume
        
        # Exhaustion Gap bestätigen
        if trend_alignment and (trend_reversal or rapid_filling):
            exhaustion_gaps.append({
                "type": "exhaustion_gap",
                "subtype": gap["type"],  # "up" oder "down"
                "idx": gap_idx,
                "size": gap["size"],
                "gap": gap["gap"],
                "pre_trend": pre_trend["direction"],
                "post_trend": post_trend["direction"],
                "filled": gap["filled"],
                "fill_idx": gap["fill_idx"],
                "rapid_filling": rapid_filling,
                "volume_declining": volume_declining,
                "trend_reversal": trend_reversal
            })
            
    return exhaustion_gaps


def detect_common_gap(df, config=None, timeframe="1d"):
    """
    Erkennt Common Gaps - gewöhnliche Kurslücken ohne besondere Bedeutung
    
    Eigenschaften:
    - Tritt oft in Seitwärtsphasen auf
    - Typischerweise kleiner als andere Gap-Typen
    - Wird meistens schnell gefüllt
    - Geringe prognostische Bedeutung
    """
    # Config laden
    if config is None:
        from patterns import get_pattern_config
        config = get_pattern_config("common_gap", PATTERN_CONFIGS.get("common_gap", {}), timeframe)
        
    max_gap_size = config.get("max_gap_size", 0.02)  # Maximale Größe (2%)
    trend_window = config.get("trend_window", 10)  # Fenster zur Analyse des Marktumfelds
    max_trend_strength = config.get("max_trend_strength", 0.5)  # Maximale Trendstärke (schwacher Trend)
    
    if len(df) < trend_window * 2:
        return []  # Nicht genug Daten
        
    # Identifiziere alle Gaps
    all_gaps = _identify_gaps(df)
    
    # Alle gefundenen Gaps
    found_breakaway = [g["idx"] for g in detect_breakaway_gap(df, config)]
    found_runaway = [g["idx"] for g in detect_runaway_gap(df, config)]
    found_exhaustion = [g["idx"] for g in detect_exhaustion_gap(df, config)]
    
    # Filtere nach Common Gaps (die, die nicht in andere Kategorien fallen)
    common_gaps = []
    
    for gap in all_gaps:
        gap_idx = gap["idx"]
        
        # Prüfe, ob dieses Gap bereits als anderer Typ klassifiziert wurde
        if gap_idx in found_breakaway or gap_idx in found_runaway or gap_idx in found_exhaustion:
            continue
            
        # Prüfe Größe des Gaps (Common Gaps sind typischerweise kleiner)
        if gap["size"] > max_gap_size:
            continue
            
        # Analysiere Marktumfeld
        pre_trend = _analyze_trend(df, max(0, gap_idx - trend_window), gap_idx - 1)
        post_trend = _analyze_trend(df, gap_idx, min(len(df) - 1, gap_idx + trend_window))
        
        # Common Gaps treten typischerweise in schwachen Trendphasen auf
        weak_trend = pre_trend["strength"] < max_trend_strength and post_trend["strength"] < max_trend_strength
        sideways_market = pre_trend["direction"] == "sideways" or post_trend["direction"] == "sideways"
        
        # Common Gaps werden typischerweise schnell gefüllt
        filled_quickly = gap["filled"] and (gap["fill_idx"] - gap_idx) <= 3
        
        # Common Gap bestätigen
        if weak_trend or sideways_market or filled_quickly:
            common_gaps.append({
                "type": "common_gap",
                "subtype": gap["type"],  # "up" oder "down"
                "idx": gap_idx,
                "size": gap["size"],
                "gap": gap["gap"],
                "pre_trend": pre_trend["direction"],
                "post_trend": post_trend["direction"],
                "filled": gap["filled"],
                "fill_idx": gap["fill_idx"],
                "filled_quickly": filled_quickly
            })
            
    return common_gaps


def render_breakaway_gap(ax, df, pattern):
    """
    Zeichnet ein Breakaway Gap auf die Achse
    """
    # Gap-Index
    gap_idx = pattern['idx']

    # Vor- und Nach-Gap-Kerze finden
    if gap_idx > 0 and gap_idx < len(df):
        pre_gap_idx = gap_idx - 1

        # Färbung je nach Gap-Typ
        color = 'lime' if pattern['subtype'] == 'up' else 'red'

        # Gap visualisieren durch Rechteck zwischen Schlusskurs der Vorkerze und Eröffnungskurs der Gap-Kerze
        gap_start = df['close'].iloc[pre_gap_idx]
        gap_end = df['open'].iloc[gap_idx]

        # Zeichne das Gap als halbtransparentes Rechteck
        ax.axhspan(min(gap_start, gap_end), max(gap_start, gap_end),
                   xmin=(gap_idx - 0.4) / len(df), xmax=(gap_idx + 0.4) / len(df),
                   alpha=0.3, color=color, edgecolor=color, linewidth=2)

        # Markiere die Kerzen vor und nach dem Gap
        ax.scatter(pre_gap_idx, df['close'].iloc[pre_gap_idx], color='white', s=60, marker='o')
        ax.scatter(gap_idx, df['open'].iloc[gap_idx], color=color, s=60, marker='o')

        # Bei bestätigten Patterns: Kursziel zeichnen
        if pattern.get('target') is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color=color, linestyle=':', alpha=0.5,
                       xmin=gap_idx / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (neben dem Gap)
        text_pos_x = gap_idx
        text_pos_y = df['close'].iloc[gap_idx] * (1.05 if pattern['subtype'] == 'up' else 0.95)

        # Färbung je nach Gap-Richtung
        bg_color = 'green' if pattern['subtype'] == 'up' else 'red'

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor=bg_color, alpha=0.3))


def render_runaway_gap(ax, df, pattern):
    """
    Zeichnet ein Runaway Gap (Measuring Gap) auf die Achse
    """
    # Gap-Index
    gap_idx = pattern['idx']

    # Vor- und Nach-Gap-Kerze finden
    if gap_idx > 0 and gap_idx < len(df):
        pre_gap_idx = gap_idx - 1

        # Färbung je nach Gap-Typ
        color = 'lime' if pattern['subtype'] == 'up' else 'red'

        # Gap visualisieren durch Rechteck zwischen Schlusskurs der Vorkerze und Eröffnungskurs der Gap-Kerze
        gap_start = df['close'].iloc[pre_gap_idx]
        gap_end = df['open'].iloc[gap_idx]

        # Zeichne das Gap als halbtransparentes Rechteck
        ax.axhspan(min(gap_start, gap_end), max(gap_start, gap_end),
                   xmin=(gap_idx - 0.4) / len(df), xmax=(gap_idx + 0.4) / len(df),
                   alpha=0.3, color=color, edgecolor=color, linewidth=2)

        # Markiere die Kerzen vor und nach dem Gap
        ax.scatter(pre_gap_idx, df['close'].iloc[pre_gap_idx], color='white', s=60, marker='o')
        ax.scatter(gap_idx, df['open'].iloc[gap_idx], color=color, s=60, marker='o')

        # Trend-Richtung anzeigen
        arrow_marker = '^' if pattern['subtype'] == 'up' else 'v'
        ax.scatter(gap_idx + 2, df['close'].iloc[min(gap_idx + 2, len(df) - 1)],
                   color=color, s=80, marker=arrow_marker)

        # Bei bestätigten Patterns: Kursziel zeichnen
        if pattern.get('target') is not None:
            target_y = pattern['target']
            ax.axhline(y=target_y, color=color, linestyle=':', alpha=0.5,
                       xmin=gap_idx / len(df), xmax=1.0)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (neben dem Gap)
        gap_idx = pattern['idx']
        # Färbung je nach Gap-Richtung
        bg_color = 'lime' if pattern['subtype'] == 'up' else 'red'
        text_pos_x = gap_idx
        text_pos_y = df['close'].iloc[gap_idx] * (1.05 if pattern['subtype'] == 'up' else 0.95)

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor=bg_color, alpha=0.3))


def render_exhaustion_gap(ax, df, pattern):
    """
    Zeichnet ein Exhaustion Gap auf die Achse
    """
    # Gap-Index
    gap_idx = pattern['idx']

    # Vor- und Nach-Gap-Kerze finden
    if gap_idx > 0 and gap_idx < len(df):
        pre_gap_idx = gap_idx - 1

        # Färbung je nach Gap-Typ
        color = 'lime' if pattern['subtype'] == 'up' else 'red'

        # Gap visualisieren durch Rechteck zwischen Schlusskurs der Vorkerze und Eröffnungskurs der Gap-Kerze
        gap_start = df['close'].iloc[pre_gap_idx]
        gap_end = df['open'].iloc[gap_idx]

        # Zeichne das Gap als halbtransparentes Rechteck
        ax.axhspan(min(gap_start, gap_end), max(gap_start, gap_end),
                   xmin=(gap_idx - 0.4) / len(df), xmax=(gap_idx + 0.4) / len(df),
                   alpha=0.3, color=color, edgecolor=color, linewidth=2)

        # Markiere die Kerzen vor und nach dem Gap
        ax.scatter(pre_gap_idx, df['close'].iloc[pre_gap_idx], color='white', s=60, marker='o')
        ax.scatter(gap_idx, df['open'].iloc[gap_idx], color=color, s=60, marker='o')

        # Wenn das Gap gefüllt wurde, markiere den Füllungspunkt
        if pattern.get('filled') and pattern.get('fill_idx') is not None:
            fill_idx = pattern['fill_idx']
            fill_color = 'red' if pattern['subtype'] == 'up' else 'lime'
            ax.scatter(fill_idx, df['close'].iloc[fill_idx],
                       color=fill_color, s=60, marker='x')

            # Verbindungslinie zwischen Gap und Füllungspunkt
            ax.plot([gap_idx, fill_idx], [df['open'].iloc[gap_idx], df['close'].iloc[fill_idx]],
                    color=fill_color, linestyle='--', alpha=0.5)

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (neben dem Gap)
        gap_idx = pattern['idx']
        # Färbung je nach Gap-Richtung
        bg_color = 'lime' if pattern['subtype'] == 'up' else 'red'
        text_pos_x = gap_idx
        text_pos_y = df['close'].iloc[gap_idx] * (1.05 if pattern['subtype'] == 'up' else 0.95)

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor=bg_color, alpha=0.3))


def render_common_gap(ax, df, pattern):
    """
    Zeichnet ein Common Gap auf die Achse
    """
    # Gap-Index
    gap_idx = pattern['idx']

    # Vor- und Nach-Gap-Kerze finden
    if gap_idx > 0 and gap_idx < len(df):
        pre_gap_idx = gap_idx - 1

        # Färbung je nach Gap-Typ
        color = 'gray'  # Common Gaps weniger hervorheben

        # Gap visualisieren durch Rechteck zwischen Schlusskurs der Vorkerze und Eröffnungskurs der Gap-Kerze
        gap_start = df['close'].iloc[pre_gap_idx]
        gap_end = df['open'].iloc[gap_idx]

        # Zeichne das Gap als halbtransparentes Rechteck
        ax.axhspan(min(gap_start, gap_end), max(gap_start, gap_end),
                   xmin=(gap_idx - 0.4) / len(df), xmax=(gap_idx + 0.4) / len(df),
                   alpha=0.2, color=color, edgecolor=color, linewidth=1)

        # Wenn das Gap gefüllt wurde, markiere den Füllungspunkt
        if pattern.get('filled') and pattern.get('fill_idx') is not None:
            fill_idx = pattern['fill_idx']
            ax.scatter(fill_idx, df['close'].iloc[fill_idx],
                       color=color, s=40, marker='x')

    # NEU: Stärke-Indikator anzeigen
    if 'strength' in pattern and SHOW_STRENGTH_IN_CHART:
        strength = pattern['strength']

        # Position für Stärke-Anzeige (neben dem Gap)
        gap_idx = pattern['idx']
        # Common Gaps haben meist geringe Bedeutung, daher neutrale Farbe
        bg_color = 'gray'
        text_pos_x = gap_idx
        text_pos_y = df['close'].iloc[gap_idx] * (1.05 if pattern['subtype'] == 'up' else 0.95)

        # Größe und Transparenz je nach Stärke
        text_size = 8 + int(strength * 4)
        text_alpha = 0.5 + (strength * 0.5)

        # Stärke als Text anzeigen
        ax.text(text_pos_x, text_pos_y, f"Stärke: {strength:.2f}", ha='center', va='center',
                fontsize=text_size, alpha=text_alpha, color='white',
                bbox=dict(facecolor=bg_color, alpha=0.3))


def render_gaps_pattern(ax, df, pattern):
    """
    Rendert ein Gap-Pattern basierend auf seinem Typ
    """
    pattern_type = pattern.get("type", "")

    if pattern_type == "breakaway_gap":
        render_breakaway_gap(ax, df, pattern)
    elif pattern_type == "runaway_gap":
        render_runaway_gap(ax, df, pattern)
    elif pattern_type == "exhaustion_gap":
        render_exhaustion_gap(ax, df, pattern)
    elif pattern_type == "common_gap":
        render_common_gap(ax, df, pattern)
    else:
        print(f"Unbekannter Pattern-Typ für Gaps: {pattern_type}")