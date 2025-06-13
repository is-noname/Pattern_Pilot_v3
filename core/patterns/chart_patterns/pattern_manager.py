# patterns/pattern_manager.py
from typing import Dict, List, Any, Optional, Set, Union
import pandas as pd

# Pattern-Kategorien importieren
from .pattern_categories import ALL_BULLISH, ALL_BEARISH, ALL_NEUTRAL
# Pattern-Detektoren importieren (wir nutzen die vorhandene Registry)
from . import PATTERN_DETECTORS, PATTERN_RENDERERS
# Config-Helfer importieren
from . import get_pattern_config
from config import TIMEFRAME_CONFIGS, PATTERN_CONFIGS


class PatternManager:
    """
    Zentrale Schnittstelle für die Pattern-Erkennung.
    Kapselt alle einzelnen Pattern-Detektoren und bietet eine einheitliche API.
    """

    def __init__(self):
        """Initialisierung des Pattern Managers"""
        # Möglicher Cache für wiederholte Analysen
        self._cache = {}
        # Registry der verfügbaren Pattern-Detektoren (nutzt die bestehende)
        self.detectors = PATTERN_DETECTORS
        # Registry der Pattern-Renderer
        self.renderers = PATTERN_RENDERERS

    def detect_patterns(self, df: pd.DataFrame, timeframe: str = "1d",
                        pattern_types: Optional[List[str]] = None,
                        use_cache: bool = True, state=None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Erkennt alle oder bestimmte Patterns im DataFrame

        Args:
            df: DataFrame mit OHLCV-Daten
            timeframe: Zeitrahmen (1d, 3d, 1w, 1M)
            pattern_types: Optional Liste mit zu erkennenden Pattern-Typen
            use_cache: Cache für wiederholte Analysen nutzen
            state: Optional AnalysisState-Objekt für timeframe-übergreifende Analyse

        Returns:
            Dict mit Pattern-Typen als Keys und Listen von Pattern-Objekten als Values
        """
        # Cache-Key erstellen (basierend auf DataFrame-Hash und Timeframe)
        if use_cache:
            cache_key = f"{hash(df.to_json())}-{timeframe}"
            if pattern_types:
                cache_key += f"-{','.join(sorted(pattern_types))}"

            # Cache-Hit prüfen
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Pattern-Typen filtern, falls angegeben
        detectors_to_use = self.detectors
        if pattern_types:
            detectors_to_use = {k: v for k, v in self.detectors.items() if k in pattern_types}

        # Pattern-Erkennung durchführen (nutzt bestehende Logik)
        results = {}

        for pattern_name, detector_func in detectors_to_use.items():
            try:
                # Timeframe-spezifische Konfiguration
                config = get_pattern_config(pattern_name, None, timeframe)

                # Pattern Detection durchführen
                patterns = detector_func(df, config, timeframe)

                # Stärke berechnen, falls State verfügbar
                if state is not None and patterns:
                    for pattern in patterns:
                        try:
                            from utils.pattern_strength import calculate_pattern_strength
                            pattern['strength'] = calculate_pattern_strength(
                                pattern, pattern_name, df, timeframe, state
                            )
                        except Exception as e:
                            print(f"⚠️ Stärkeberechnung für {pattern_name} fehlgeschlagen: {e}")
                            pattern['strength'] = 0.5  # Fallback

                # Ergebnis speichern
                results[pattern_name] = patterns

            except Exception as e:
                print(f"❌ Fehler bei {pattern_name}: {e}")
                import traceback
                traceback.print_exc()
                results[pattern_name] = []

        # Cache aktualisieren
        if use_cache:
            self._cache[cache_key] = results

        return results

    def get_patterns_by_category(self, patterns: Dict[str, List[Dict[str, Any]]],
                                 category: str = "all") -> Dict[str, List[Dict[str, Any]]]:
        """
        Filtert Patterns nach Kategorie (bullish, bearish, neutral, all)

        Args:
            patterns: Dict mit Pattern-Ergebnissen
            category: Kategorie ("bullish", "bearish", "neutral", "all")

        Returns:
            Gefiltertes Dict mit Patterns
        """
        if category == "all":
            return patterns

        # Pattern-Listen für die Filterung
        filter_lists = {
            "bullish": ALL_BULLISH,
            "bearish": ALL_BEARISH,
            "neutral": ALL_NEUTRAL
        }

        if category not in filter_lists:
            raise ValueError(f"Unbekannte Kategorie: {category}. Erlaubt: bullish, bearish, neutral, all")

        # Nach Kategorie filtern
        return {
            pattern_type: pattern_list
            for pattern_type, pattern_list in patterns.items()
            if pattern_type in filter_lists[category]
        }

    def get_patterns_by_confirmation(self, patterns: Dict[str, List[Dict[str, Any]]],
                                     confirmed_only: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filtert Patterns nach Bestätigungsstatus

        Args:
            patterns: Dict mit Pattern-Ergebnissen
            confirmed_only: Nur bestätigte Patterns zurückgeben

        Returns:
            Gefiltertes Dict mit Patterns
        """
        if not confirmed_only:
            return patterns

        # Nach Bestätigung filtern
        filtered_patterns = {}

        for pattern_type, pattern_list in patterns.items():
            confirmed_patterns = [p for p in pattern_list if p.get('confirmed', False)]
            if confirmed_patterns:
                filtered_patterns[pattern_type] = confirmed_patterns

        return filtered_patterns

    def get_pattern_count(self, patterns: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """
        Liefert Statistiken über die erkannten Patterns

        Args:
            patterns: Dict mit Pattern-Ergebnissen

        Returns:
            Dict mit Statistiken
        """
        stats = {
            "total": 0,
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "confirmed": 0,
            "unconfirmed": 0
        }

        for pattern_type, pattern_list in patterns.items():
            # Gesamtzahl
            stats["total"] += len(pattern_list)

            # Nach Richtung zählen
            if pattern_type in ALL_BULLISH:
                stats["bullish"] += len(pattern_list)
            elif pattern_type in ALL_BEARISH:
                stats["bearish"] += len(pattern_list)
            else:
                stats["neutral"] += len(pattern_list)

            # Nach Bestätigung zählen
            for pattern in pattern_list:
                if pattern.get('confirmed', False):
                    stats["confirmed"] += 1
                else:
                    stats["unconfirmed"] += 1

        return stats

    def clear_cache(self):
        """Löscht den Pattern-Cache"""
        self._cache = {}
        print("🧹 Pattern-Cache geleert")

    def get_available_patterns(self) -> List[str]:
        """Gibt eine Liste aller verfügbaren Pattern-Typen zurück"""
        return list(self.detectors.keys())

    def get_pattern_categories(self) -> Dict[str, List[str]]:
        """Gibt Pattern-Typen nach Kategorie gruppiert zurück"""
        return {
            "bullish": ALL_BULLISH.copy(),
            "bearish": ALL_BEARISH.copy(),
            "neutral": ALL_NEUTRAL.copy()
        }


# Singleton-Instanz für einfache Verwendung
pattern_manager = PatternManager()