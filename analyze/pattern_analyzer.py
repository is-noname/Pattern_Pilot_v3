# analyze/pattern_analyzer.py
import pandas as pd
from typing import Dict, Any, List
from core.patterns.formation_patterns.pattern_categories import ALL_BULLISH, ALL_BEARISH, ALL_NEUTRAL
from utils.pattern_strength import calculate_pattern_strength
from analyze.timeframe_conflict_analyzer import TimeframeConflictAnalyzer

class PatternAnalyzer:
    """
    Analysiert erkannte Chart-Patterns und bewertet diese

    Funktionen:
    - Berechnung der Pattern-Stärke
    - Ableitung von Handelsempfehlungen
    - Bestimmung von Support/Resistance-Levels
    - Erkennung von Multi-Timeframe-Konflikten
    """

    def __init__(self, state=None):
        # AnalysisState-Objekt mit allen Timeframe-Daten
        self.state = state
        # TimeframeConflictAnalyzer
        self.timeframe_hierarchy = ["1d", "3d", "1w", "1m"]
        self.conflict_analyzer = TimeframeConflictAnalyzer(self.timeframe_hierarchy)

    # Analysiert erkannte Patterns im DataFrame
    def analyze_patterns(self, patterns, df, timeframe):
        """
        Analysiert erkannte Patterns im DataFrame

        Args:
            patterns: Dict mit erkannten Patterns
            df: DataFrame mit Preisdaten
            timeframe: Zeitrahmen der Analyse

        Returns:
            Dict mit erweiterten Pattern-Informationen
        """
        if not patterns:
            return {}

        result = {}

        for pattern_type, pattern_list in patterns.items():
            # Patterns mit zusätzlichen Informationen anreichern
            enhanced_patterns = []

            for pattern in pattern_list:
                # Stärke berechnen
                pattern['strength'] = calculate_pattern_strength(
                    pattern, pattern_type, df, timeframe, self.state
                )

                # Richtung bestimmen
                pattern['direction'] = self._get_pattern_direction(pattern_type)

                # Risiko-Ertrags-Verhältnis berechnen
                if pattern.get('confirmed', False) and pattern.get('target') and pattern.get('stop_loss'):
                    current_price = df['close'].iloc[-1]
                    risk = abs(current_price - pattern['stop_loss'])
                    reward = abs(pattern['target'] - current_price)

                    if risk > 0:
                        pattern['risk_reward_ratio'] = reward / risk
                    else:
                        pattern['risk_reward_ratio'] = None

                enhanced_patterns.append(pattern)

            result[pattern_type] = enhanced_patterns

        return result

    # Gibt die stärksten Patterns zurück, gefiltert nach Mindeststärke
    def get_strongest_patterns(self, patterns, min_strength=0.6, limit=3):
        """
        Gibt die stärksten Patterns zurück, gefiltert nach Mindeststärke
        """
        flat_patterns = []

        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern.get('strength', 0) >= min_strength:
                    flat_patterns.append({
                        'type': pattern_type,
                        'data': pattern
                    })

        # Nach Stärke sortieren
        flat_patterns.sort(key=lambda x: x['data'].get('strength', 0), reverse=True)

        return flat_patterns[:limit]

    # Gibt die Richtung eines Patterns
    def _get_pattern_direction(self, pattern_type):
        """Bestimmt die Richtung eines Patterns (bullish, bearish, neutral)"""
        if pattern_type in ALL_BULLISH:
            return "bullish"
        elif pattern_type in ALL_BEARISH:
            return "bearish"
        else:
            return "neutral"

    # Analysiert Konflikte zwischen verschiedenen Timeframes
    def analyze_timeframe_conflicts(self, timeframe_data, timeframe_patterns):
        """
        Analysiert Konflikte zwischen verschiedenen Timeframes

        Args:
            timeframe_data: Dict mit OHLCV-Daten pro Timeframe
            timeframe_patterns: Dict mit erkannten Patterns pro Timeframe

        Returns:
            Liste mit Konfliktobjekten
        """
        if len(timeframe_data) < 2:  # Mindestens 2 Timeframes für Konfliktanalyse nötig
            return []

        return self.conflict_analyzer.analyze_all_conflicts(
            timeframe_data, timeframe_patterns
        )

    # Extrahiert wichtige S/R-Levels aus allen Timeframes
    def extract_key_levels(self, timeframe_data, timeframe_patterns):
        """
        Extrahiert wichtige Support- und Resistance-Levels aus allen Timeframes

        Returns:
            Dict mit Support/Resistance-Levels
        """
        # Diese Methode nutzt die interne Methode des conflict_analyzer
        sr_levels = self.conflict_analyzer._extract_sr_levels(
            timeframe_data, timeframe_patterns
        )

        # Levels nach Bedeutung sortieren und zusammenfassen
        consolidated_levels = {
            'support': [],
            'resistance': []
        }

        # Gewichtung nach Timeframe
        tf_weights = {
            "1d": 1.0,
            "3d": 1.5,
            "1w": 2.0,
            "1m": 3.0
        }

        for tf, levels in sr_levels.items():
            weight = tf_weights.get(tf, 1.0)

            for level in levels:
                level_type = level.get('type')
                if level_type in ['support', 'resistance']:
                    # Level mit Gewichtung versehen
                    weighted_level = level.copy()
                    weighted_level['timeframe'] = tf
                    weighted_level['importance'] = level.get('strength', 0.5) * weight

                    consolidated_levels[level_type].append(weighted_level)

        # Nach Wichtigkeit sortieren
        for key in consolidated_levels:
            consolidated_levels[key].sort(key=lambda x: x.get('importance', 0), reverse=True)

        return consolidated_levels

    # Generiert Handelsempfehlung auf Basis der erkannten Patterns
    def generate_trading_recommendation(self, patterns, current_price, timeframe="1d"):
        """
        Generiert eine Handelsempfehlung basierend auf den erkannten Patterns

        Args:
            patterns: Dict mit analysierten Patterns
            current_price: Aktueller Preis
            timeframe: Zeitrahmen der Analyse

        Returns:
            Dict mit Handelsempfehlung
        """
        if not patterns:
            return {
                "action": "NEUTRAL",
                "confidence": 0.0,
                "reason": "Keine Patterns erkannt",
                "risk_level": "UNKNOWN"
            }

        # Stärkste Patterns holen
        strongest = self.get_strongest_patterns(patterns, min_strength=0.5, limit=3)

        if not strongest:
            return {
                "action": "NEUTRAL",
                "confidence": 0.0,
                "reason": "Keine signifikanten Patterns erkannt",
                "risk_level": "UNKNOWN"
            }

        # Richtungs-Zusammenfassung
        bullish_count = sum(1 for p in strongest if p['data'].get('direction') == 'bullish')
        bearish_count = sum(1 for p in strongest if p['data'].get('direction') == 'bearish')

        # Top-Pattern für Begründung
        top_pattern = strongest[0]
        pattern_type = top_pattern['type'].replace('_', ' ').title()

        # Bestimmung der Handlung
        action = "NEUTRAL"
        reason = f"Gemischte Signale mit {pattern_type} als stärkstem Muster"
        confidence = strongest[0]['data'].get('strength', 0.5)

        if bullish_count > bearish_count:
            action = "BUY"
            reason = f"Überwiegend bullische Patterns, angeführt von {pattern_type}"
        elif bearish_count > bullish_count:
            action = "SELL"
            reason = f"Überwiegend bearische Patterns, angeführt von {pattern_type}"

        # Risiko-Level bestimmen
        risk_level = "MEDIUM"  # Standard

        # Ist das Top-Pattern bestätigt?
        if top_pattern['data'].get('confirmed', False):
            confidence += 0.2  # Erhöhte Konfidenz bei bestätigten Patterns

            # Risiko-Verhältnis prüfen
            if top_pattern['data'].get('risk_reward_ratio'):
                rr_ratio = top_pattern['data']['risk_reward_ratio']
                if rr_ratio > 3.0:
                    risk_level = "LOW"
                elif rr_ratio < 1.5:
                    risk_level = "HIGH"
        else:
            confidence -= 0.2  # Verringerte Konfidenz bei unbestätigten Patterns
            risk_level = "HIGH"  # Höheres Risiko bei unbestätigten Patterns

        # Konfidenz begrenzen
        confidence = max(0.1, min(0.9, confidence))

        # Support/Resistance-Level aus dem Top-Pattern extrahieren
        target = top_pattern['data'].get('target')
        stop_loss = top_pattern['data'].get('stop_loss')

        recommendation = {
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "risk_level": risk_level,
            "timeframe": timeframe,
            "based_on_pattern": pattern_type
        }

        if target:
            recommendation["target"] = target
            recommendation["target_percent"] = ((target - current_price) / current_price) * 100

        if stop_loss:
            recommendation["stop_loss"] = stop_loss
            recommendation["stop_loss_percent"] = ((stop_loss - current_price) / current_price) * 100

        return recommendation


# Singleton-Instanz für einfache Verwendung
pattern_analyzer = PatternAnalyzer()