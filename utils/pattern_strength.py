# utils/pattern_strength.py   !!!!! noch aus dem alten pattern pilot. evtl anpasssen!!!!!
import numpy as np
from core.patterns.chart_patterns.pattern_categories import ALL_BULLISH, ALL_BEARISH, ALL_NEUTRAL

def calculate_pattern_strength(pattern, pattern_type, df, timeframe, state):
    """
    Berechnet die Stärke eines Musters basierend auf verschiedenen Faktoren
    
    Args:
        pattern: Das Muster-Objekt
        pattern_type: Der Typ des Musters
        df: DataFrame mit den Preisdaten
        timeframe: Der aktuelle Timeframe
        state: AnalysisState-Objekt mit allen Timeframe-Daten
        
    Returns:
        Float zwischen 0 und 1, wobei 1 die höchste Stärke repräsentiert
    """
    # Basisstärke initialisieren
    base_strength = 0.5  # Neutraler Ausgangspunkt
    
    # Faktoren für die Stärkeberechnung
    factors = {
        "confirmation": 0.3,        # Bestätigung des Musters
        "timeframe_level": 0.2,     # Höhere Timeframes haben mehr Gewicht
        "pattern_quality": 0.2,     # Qualität des Musters (Größe, Symmetrie, etc.)
        "higher_tf_alignment": 0.2, # Übereinstimmung mit höheren Timeframes
        "volume_conf": 0.1,         # Volumenbestätigung
    }
    
    strength_score = 0.0
    
    # 1. Bestätigung des Musters
    if pattern.get('confirmed', False):
        strength_score += factors["confirmation"]
    
    # 2. Timeframe-Level
    tf_levels = {"1d": 0.6, "3d": 0.7, "1w": 0.8, "1m": 1.0}
    strength_score += factors["timeframe_level"] * tf_levels.get(timeframe, 0.5)
    
    # 3. Musterqualität berechnen
    pattern_quality = _calculate_pattern_quality(pattern, pattern_type, df)
    strength_score += factors["pattern_quality"] * pattern_quality
    
    # 4. Übereinstimmung mit höheren Timeframes
    higher_tf_alignment = _check_higher_timeframe_alignment(pattern, pattern_type, timeframe, state)
    strength_score += factors["higher_tf_alignment"] * higher_tf_alignment
    
    # 5. Volumenbestätigung (falls verfügbar)
    if 'volume' in df.columns and len(df['volume']) > 0:
        volume_conf = _check_volume_confirmation(pattern, pattern_type, df)
        strength_score += factors["volume_conf"] * volume_conf
    
    # Normalisieren auf 0-1 Bereich
    final_strength = base_strength + strength_score
    final_strength = max(0.0, min(1.0, final_strength))
    
    return final_strength

def _calculate_pattern_quality(pattern, pattern_type, df):
    """Berechnet die intrinsische Qualität des Musters"""
    quality = 0.5  # Standard-Mittelwert
    
    # Je nach Mustertyp unterschiedliche Qualitätskriterien
    if pattern_type == "double_bottom" or pattern_type == "double_top":
        # Bei Double-Mustern: Symmetrie und Tiefe/Höhe
        if "P1" in pattern and "P2" in pattern and "neckline" in pattern:
            # Symmetrie: wie ähnlich sind die beiden Tiefs/Hochs
            p1_val = df['low' if pattern_type == "double_bottom" else 'high'].iloc[pattern["P1"]]
            p2_val = df['low' if pattern_type == "double_bottom" else 'high'].iloc[pattern["P2"]]
            
            if p1_val != 0:  # Vermeide Division durch Null
                symmetry = 1.0 - abs(p1_val - p2_val) / p1_val
                quality = symmetry  # 0-1 Wert für Symmetrie
    
    elif "head_and_shoulders" in pattern_type:
        # Bei H&S: Symmetrie der Schultern und Kopfhöhe
        if "left_shoulder" in pattern and "right_shoulder" in pattern and "head" in pattern:
            left_val = df['high' if "inverse" not in pattern_type else 'low'].iloc[pattern["left_shoulder"]]
            right_val = df['high' if "inverse" not in pattern_type else 'low'].iloc[pattern["right_shoulder"]]
            
            if left_val != 0:  # Vermeide Division durch Null
                symmetry = 1.0 - abs(left_val - right_val) / left_val
                quality = symmetry
    
    elif "triangle" in pattern_type:
        # Bei Dreiecken: Anzahl der Berührungspunkte
        if "resistance_points" in pattern and "support_points" in pattern:
            total_touches = len(pattern["resistance_points"]) + len(pattern["support_points"])
            quality = min(1.0, max(0.4, total_touches / 10.0))  # Mehr Berührungen = besser
    
    # In future_versions: Füge weitere Mustertypen hinzu
    
    return quality

def _check_higher_timeframe_alignment(pattern, pattern_type, current_tf, state):
    """Prüft, ob das Muster mit höheren Timeframes übereinstimmt"""
    timeframe_hierarchy = ["1d", "3d", "1w", "1m"]
    
    if current_tf not in timeframe_hierarchy:
        return 0.5  # Neutral, wenn Timeframe nicht in Hierarchie
    
    current_idx = timeframe_hierarchy.index(current_tf)
    higher_tfs = timeframe_hierarchy[current_idx+1:]
    
    # Trendrichtung des aktuellen Musters bestimmen
    if pattern_type in ALL_BULLISH:
        current_direction = "bullish"
    elif pattern_type in ALL_BEARISH:
        current_direction = "bearish"
    else:
        current_direction = "neutral"
    
    # Keine höheren Timeframes verfügbar
    if not higher_tfs or not state.timeframe_patterns:
        return 0.5
    
    alignment_score = 0.0
    alignment_count = 0
    
    # Prüfe Übereinstimmung mit jedem höheren Timeframe
    for tf in higher_tfs:
        if tf not in state.timeframe_patterns:
            continue
            
        higher_patterns = state.timeframe_patterns[tf]
        if not higher_patterns:
            continue
            
        # Gibt es bestätigte bullische Muster im höheren Timeframe?
        has_bullish = any(
            higher_patterns.get(ptype, []) and 
            any(p.get('confirmed', False) for p in higher_patterns.get(ptype, []))
            for ptype in ALL_BULLISH
        )
        
        # Gibt es bestätigte bearische Muster im höheren Timeframe?
        has_bearish = any(
            higher_patterns.get(ptype, []) and 
            any(p.get('confirmed', False) for p in higher_patterns.get(ptype, []))
            for ptype in ALL_BEARISH
        )
        
        # Bewerte Übereinstimmung
        if (current_direction == "bullish" and has_bullish) or \
           (current_direction == "bearish" and has_bearish):
            # Volle Übereinstimmung
            alignment_score += 1.0
        elif (current_direction == "bullish" and has_bearish) or \
             (current_direction == "bearish" and has_bullish):
            # Gegenläufige Trends - schlecht
            alignment_score += 0.0
        else:
            # Neutraler Fall
            alignment_score += 0.5
            
        alignment_count += 1
    
    # Durchschnittliche Übereinstimmung berechnen
    if alignment_count > 0:
        return alignment_score / alignment_count
    else:
        return 0.5  # Neutral, wenn keine höheren Timeframes

def _check_volume_confirmation(pattern, pattern_type, df):
    """Prüft, ob das Volumen das Muster bestätigt"""
    if 'volume' not in df.columns:
        return 0.5  # Neutral, wenn kein Volumen verfügbar
    
    volume_score = 0.5  # Standard-Mittelwert
    
    # Bei bestätigten Mustern: Prüfe Volumen beim Ausbruch
    if pattern.get('confirmed', False) and pattern.get('breakout_idx') is not None:
        breakout_idx = pattern['breakout_idx']
        
        # Durchschnittliches Volumen vor dem Ausbruch
        pre_breakout_vol = df['volume'].iloc[max(0, breakout_idx-5):breakout_idx].mean()
        
        # Volumen beim Ausbruch
        breakout_vol = df['volume'].iloc[breakout_idx]
        
        if pre_breakout_vol > 0:  # Vermeide Division durch Null
            vol_ratio = breakout_vol / pre_breakout_vol
            
            # Bewerte Volumenbestätigung
            if vol_ratio >= 2.0:  # Hohes Ausbruchsvolumen: Sehr gut
                volume_score = 1.0
            elif vol_ratio >= 1.5:  # Erhöhtes Volumen: Gut
                volume_score = 0.8
            elif vol_ratio >= 1.0:  # Gleiches Volumen: Neutral
                volume_score = 0.5
            else:  # Niedrigeres Volumen: Schlecht
                volume_score = 0.3
    
    return volume_score