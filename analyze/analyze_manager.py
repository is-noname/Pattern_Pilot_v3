# analyze/analyze_manager.py
"""
Zentrale Schnittstelle für alle Analysekomponenten
Verhindert zirkuläre Importe durch zentrale Koordination
"""
#from patterns import detect_all_patterns
from core.patterns.formation_patterns.pattern_categories import ALL_BULLISH, ALL_BEARISH
from analyze.pattern_analyzer import PatternAnalyzer
from analyze.timeframe_conflict_analyzer import TimeframeConflictAnalyzer


class AnalyzeManager:
    """
    Manager-Klasse, die alle Analysekomponenten orchestriert
    und eine einheitliche Schnittstelle bietet
    """
    def __init__(self):
        """Initialisiert den Analyze-Manager mit allen benötigten Komponenten"""
        self.pattern_analyzer = PatternAnalyzer()
        self.conflict_analyzer = TimeframeConflictAnalyzer(["1d", "3d", "1w", "1M"])
        from cache.cache_manager import cache_instance
        self.cache = cache_instance
        
    # def _get_api_manager(self):
    #     """Lazy-Loading des API-Managers, um zirkuläre Importe zu vermeiden"""
    #     if self.api_manager is None:
    #         from api import APIManager
    #         self.api_manager = APIManager()
    #     return self.api_manager
    
    def analyze_symbol(self, symbol, days=90, timeframes=None, preferred_api=None):
        """
        Vollständige Analyse eines Symbols über alle Timeframes
        
        Returns:
            Dict mit allen Analyseergebnissen
        """
        if timeframes is None:
            timeframes = ["1d", "3d", "1w", "1M"]
        
        #api = self._get_api_manager()
        
        results = {
            'timeframe_data': {},
            'timeframe_patterns': {},
            'analyzed_patterns': {},
            'recommendations': {},
            'conflicts': [],
            'summary': {
                'total_patterns': 0,
                'confirmed_patterns': 0,
                'dominant_trend': 'neutral'
            }
        }
        
        # 1. Daten für alle Timeframes holen und Patterns erkennen
        for tf in timeframes:
            try:
                cached_data = self.cache.get_cached_data(symbol, tf)

                if cached_data is not None and not cached_data.empty:
                    # Daten in passendes Format bringen
                    # Achtung: Cache liefert nur DataFrame, kein metadata-Dictionary
                    df = cached_data

                    # Dummy-Metadata erzeugen (nur das Nötigste)
                    metadata = {
                        'identifier': symbol,
                        'timeframe': tf,
                        'pattern_ready': True  # Cache sollte immer normalisierte Daten haben
                    }

                    # Daten speichern
                    results['timeframe_data'][tf] = df

                if not cached_data['data'].empty:
                    # Daten speichern
                    results['timeframe_data'][tf] = cached_data['data']
                    
                    # Patterns erkennen
                    patterns = self.detect_all_patterns(cached_data['data'], tf)
                    results['timeframe_patterns'][tf] = patterns
                    
                    # Patterns analysieren
                    analyzed = self.pattern_analyzer.analyze_patterns(patterns, cached_data['data'], tf)
                    results['analyzed_patterns'][tf] = analyzed
                    
                    # Trading-Empfehlung erstellen
                    current_price = cached_data['data']['close'].iloc[-1]
                    recommendation = self.pattern_analyzer.generate_trading_recommendation(
                        analyzed, current_price, tf
                    )
                    results['recommendations'][tf] = recommendation
                    
                    # Statistik aktualisieren
                    pattern_count = sum(len(p) for p in patterns.values())
                    confirmed_count = sum(
                        sum(1 for p in pattern_list if p.get('confirmed', False))
                        for pattern_list in patterns.values()
                    )
                    results['summary']['total_patterns'] += pattern_count
                    results['summary']['confirmed_patterns'] += confirmed_count
                    
            except Exception as e:
                print(f"Fehler bei {tf} Analyse: {e}")
        
        # 2. Konflikte zwischen Timeframes analysieren
        if len(results['timeframe_data']) >= 2:
            results['conflicts'] = self.conflict_analyzer.analyze_all_conflicts(
                results['timeframe_data'],
                results['timeframe_patterns']
            )
        
        # 3. Dominanten Trend bestimmen
        results['summary']['dominant_trend'] = self._determine_dominant_trend(results)
        
        # 4. Key Levels extrahieren
        results['summary']['key_levels'] = self._extract_key_levels(results)
        
        # 5. Finale Empfehlung
        results['final_recommendation'] = self._get_final_recommendation(results)
        
        return results
    
    def _determine_dominant_trend(self, results):
        """Bestimmt dominanten Trend über alle Timeframes"""
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
        
        if bullish_score > bearish_score * 1.5:
            return "strongly_bullish"
        elif bullish_score > bearish_score * 1.2:
            return "bullish"
        elif bearish_score > bullish_score * 1.5:
            return "strongly_bearish"
        elif bearish_score > bullish_score * 1.2:
            return "bearish"
        else:
            return "neutral"
    
    def _extract_key_levels(self, results):
        """Extrahiert wichtige Support- und Resistance-Levels über alle Timeframes"""
        # SR-Levels aus dem Conflict Analyzer
        sr_levels = self.conflict_analyzer._extract_sr_levels(
            results['timeframe_data'],
            results['timeframe_patterns']
        )
        
        # Sammle alle Level mit Gewichtung nach Timeframe
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
        
        return all_levels[:10]  # Top 10 Level
    
    def _get_final_recommendation(self, results):
        """Erzeugt eine finale Handelsempfehlung basierend auf allen Timeframes"""
        # Primär: Empfehlung vom kürzesten Timeframe (1d)
        if "1d" in results['recommendations']:
            primary_rec = results['recommendations']["1d"]
        elif results['recommendations']:
            # Alternativ: Erste verfügbare Empfehlung
            primary_rec = next(iter(results['recommendations'].values()))
        else:
            return None
        
        # Konflikte berücksichtigen
        conflict_severity = sum(
            3 if c.get('severity') == 'major' else 
            2 if c.get('severity') == 'moderate' else 
            1 for c in results['conflicts']
        )
        
        # Bei schweren Konflikten: Vorsichtiger sein
        if conflict_severity >= 5 and primary_rec['action'] in ['BUY', 'SELL']:
            adjusted_rec = primary_rec.copy()
            adjusted_rec['action'] = 'CAUTION'
            adjusted_rec['reason'] = f"Ursprünglich {primary_rec['action']}, aber hohe Konflikte zwischen Timeframes"
            adjusted_rec['risk_level'] = 'HIGH'
            return adjusted_rec
        
        return primary_rec


# Globale Instanz zur einfachen Verwendung
analyze_manager = AnalyzeManager()