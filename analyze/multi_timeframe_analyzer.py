# utils/multi_timeframe_analyzer.py
from analyze.timeframe_conflict_analyzer import TimeframeConflictAnalyzer
from api import APIManager
from patterns import detect_all_patterns


class MultiTimeframeAnalyzer:
    """Multi-Timeframe-Analyse mit Konfliktdetektion - UI-agnostisch"""

    def __init__(self):
        self.timeframes = ["1d", "3d", "1w", "1M"]
        self.conflict_analyzer = TimeframeConflictAnalyzer(self.timeframes)
        from cache.cache_manager import cache_instance
        self.cache = cache_instance

    def analyze_all_timeframes(self, identifier, days=180):
        """Analysiert alle Timeframes und erkennt Konflikte"""
        print(f"🔍 Multi-Timeframe Analyse für {identifier}")

        results = {
            'timeframe_data': {},
            'timeframe_patterns': {},
            'conflicts': [],
            'summary': {}
        }

        # 1. Daten für alle Timeframes aus dem Cache holen
        for tf in self.timeframes:
            try:
                print(f"📊 Lade {tf} Daten aus Cache...")
                cached_data = self.cache.get_cached_data(identifier, tf)

                if cached_data is not None and not cached_data.empty:
                    results['timeframe_data'][tf] = cached_data

                    # Pattern-Detection für diesen Timeframe
                    patterns = detect_all_patterns(cached_data, tf)
                    results['timeframe_patterns'][tf] = patterns

                    print(f"✅ {tf}: {len(cached_data)} Datenpunkte, {sum(len(p) for p in patterns.values())} Patterns")
                else:
                    print(f"❌ {tf}: Keine Daten im Cache")

            except Exception as e:
                print(f"❌ {tf} Cache-Fehler: {e}")

        # 2. Konflikte analysieren
        if len(results['timeframe_data']) >= 2:
            print("🔄 Analysiere Timeframe-Konflikte...")
            results['conflicts'] = self.conflict_analyzer.analyze_all_conflicts(
                results['timeframe_data'],
                results['timeframe_patterns']
            )
            print(f"⚠️ {len(results['conflicts'])} Konflikte gefunden")

        # 3. Zusammenfassung erstellen
        results['summary'] = self._create_summary(results)

        return results

    def _create_summary(self, results):
        """Erstellt Analyse-Zusammenfassung"""
        summary = {
            'total_timeframes': len(results['timeframe_data']),
            'total_patterns': sum(
                sum(len(p) for p in patterns.values())
                for patterns in results['timeframe_patterns'].values()
            ),
            'total_conflicts': len(results['conflicts']),
            'severity_breakdown': {
                'major': 0,
                'moderate': 0,
                'minor': 0
            },
            'dominant_trend': self._determine_dominant_trend(results),
            'key_levels': self._extract_key_levels(results)
        }

        # Konflikte nach Schweregrad aufteilen
        for conflict in results['conflicts']:
            severity = conflict.get('severity', 'minor')
            summary['severity_breakdown'][severity] += 1

        return summary

    def _determine_dominant_trend(self, results):
        """Bestimmt dominanten Trend über alle Timeframes"""
        if not results['timeframe_patterns']:
            return "neutral"

        from patterns.pattern_categories import ALL_BULLISH, ALL_BEARISH

        bullish_score = 0
        bearish_score = 0

        # Gewichtung: Längere Timeframes haben mehr Einfluss
        weights = {"1d": 1, "3d": 2, "1w": 3, "1M": 4}

        for tf, patterns in results['timeframe_patterns'].items():
            weight = weights.get(tf, 1)

            for pattern_type, pattern_list in patterns.items():
                confirmed_patterns = [p for p in pattern_list if p.get('confirmed', False)]

                if pattern_type in ALL_BULLISH:
                    bullish_score += len(confirmed_patterns) * weight
                elif pattern_type in ALL_BEARISH:
                    bearish_score += len(confirmed_patterns) * weight

        if bullish_score > bearish_score * 1.2:
            return "bullish"
        elif bearish_score > bullish_score * 1.2:
            return "bearish"
        else:
            return "neutral"

    def _extract_key_levels(self, results):
        """Extrahiert wichtige S/R-Level über alle Timeframes"""
        key_levels = []

        # Nutze die S/R-Extraktion aus dem Conflict Analyzer
        sr_levels = self.conflict_analyzer._extract_sr_levels(
            results['timeframe_data'],
            results['timeframe_patterns']
        )

        # Sammle alle Level und gewichte nach Timeframe
        all_levels = []
        weights = {"1d": 1, "3d": 2, "1w": 3, "1M": 4}

        for tf, levels in sr_levels.items():
            weight = weights.get(tf, 1)
            for level in levels:
                all_levels.append({
                    'price': level['price'],
                    'type': level['type'],
                    'timeframe': tf,
                    'weight': weight * level.get('strength', 0.5)
                })

        # Sortiere nach Gewichtung
        all_levels.sort(key=lambda x: x['weight'], reverse=True)

        return all_levels[:5]  # Top 5 Level

    def get_trading_recommendation(self, analysis_result):
        """Trading-Empfehlung basierend auf Multi-Timeframe-Analyse"""
        conflicts = analysis_result['conflicts']
        summary = analysis_result['summary']

        # Risiko-Score basierend auf Konflikten
        risk_score = 0
        for conflict in conflicts:
            if conflict['severity'] == 'major':
                risk_score += 3
            elif conflict['severity'] == 'moderate':
                risk_score += 2
            else:
                risk_score += 1

        # Empfehlung generieren
        if risk_score >= 6:
            recommendation = {
                'action': 'AVOID',
                'reason': 'Hohe Konflikte zwischen Timeframes',
                'risk_level': 'HIGH'
            }
        elif risk_score >= 3:
            recommendation = {
                'action': 'CAUTION',
                'reason': 'Moderate Konflikte - nur mit engem Stop-Loss',
                'risk_level': 'MEDIUM'
            }
        else:
            # Basierend auf dominantem Trend
            trend = summary['dominant_trend']
            if trend == 'bullish':
                recommendation = {
                    'action': 'BUY',
                    'reason': 'Bullish über mehrere Timeframes',
                    'risk_level': 'LOW'
                }
            elif trend == 'bearish':
                recommendation = {
                    'action': 'SELL',
                    'reason': 'Bearish über mehrere Timeframes',
                    'risk_level': 'LOW'
                }
            else:
                recommendation = {
                    'action': 'HOLD',
                    'reason': 'Neutraler Trend - abwarten',
                    'risk_level': 'MEDIUM'
                }

        # Key Levels hinzufügen
        key_levels = summary['key_levels']
        if key_levels:
            nearest_support = min([l for l in key_levels if l['type'] == 'support'],
                                  key=lambda x: abs(x['price']), default=None)
            nearest_resistance = min([l for l in key_levels if l['type'] == 'resistance'],
                                     key=lambda x: abs(x['price']), default=None)

            recommendation['support'] = nearest_support['price'] if nearest_support else None
            recommendation['resistance'] = nearest_resistance['price'] if nearest_resistance else None

        return recommendation

    # ---


# UPDATE
"""
Utils Module - Hilfsfunktionen und Tools
"""

from utils.data_validator import DataValidator
from utils.timeframe_aggregator import TimeframeAggregator, aggregate_daily_to_timeframe, is_aggregation_needed
from analyze.timeframe_conflict_analyzer import TimeframeConflictAnalyzer
from analyze.multi_timeframe_analyzer import MultiTimeframeAnalyzer

__all__ = [
    'DataValidator',
    'TimeframeAggregator',
    'aggregate_daily_to_timeframe',
    'is_aggregation_needed',
    'TimeframeConflictAnalyzer',
    'MultiTimeframeAnalyzer'
]
