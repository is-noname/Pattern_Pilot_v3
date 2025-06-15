# timeframe_conflict_analyzer.py
import numpy as np
from core.patterns.formation_patterns.pattern_categories import ALL_BULLISH, ALL_BEARISH, ALL_NEUTRAL


class TimeframeConflictAnalyzer:
    """
    Erweiterte Analyse von Konflikten zwischen verschiedenen Timeframes.
    Erkennt Support/Resistance-Konflikte, Trendkonflikte und Volumen-Diskrepanzen.
    """

    def __init__(self, timeframe_hierarchy):
        self.timeframe_hierarchy = timeframe_hierarchy
        self.timeframe_order = ["1d", "3d", "1w", "1m"]  # Von kurz zu lang

    # ++++ Konflikte ++++
    # Analysiert Konflikte zwischen den Timeframes
    def analyze_all_conflicts(self, timeframe_data, timeframe_patterns):
        """
        Analysiert alle möglichen Konflikte zwischen den Timeframes.

        Args:
            timeframe_data: Dict mit OHLCV-Daten pro Timeframe
            timeframe_patterns: Dict mit erkannten Mustern pro Timeframe

        Returns:
            Liste mit Konfliktobjekten
        """
        conflicts = []

        # 1. Trend-Richtungskonflikte
        conflicts.extend(self.detect_trend_direction_conflicts(timeframe_patterns))

        # 2. Support/Resistance-Konflikte
        conflicts.extend(self.detect_support_resistance_conflicts(timeframe_data, timeframe_patterns))

        # 3. Volumenbestätigungskonflikte
        conflicts.extend(self.detect_volume_confirmation_conflicts(timeframe_data, timeframe_patterns))

        # 4. Marktphasen-Konflikte (langfristig vs. kurzfristig)
        conflicts.extend(self.detect_market_phase_conflicts(timeframe_data, timeframe_patterns))

        # Konfliktbewertung (Schweregrad)
        self._rate_conflict_severity(conflicts)

        return conflicts

    # Erkennt Konflikte zwischen Trendrichtungen in Timeframes
    def detect_trend_direction_conflicts(self, timeframe_patterns):
        """
        Erkennt Konflikte zwischen Trendrichtungen in verschiedenen Timeframes.
        z.B. bullisches Muster in 1d vs. bearisches Muster in 1w
        """
        conflicts = []

        for i, tf1 in enumerate(self.timeframe_order):
            if tf1 not in timeframe_patterns:
                continue

            for tf2 in self.timeframe_order[i + 1:]:
                if tf2 not in timeframe_patterns:
                    continue

                # Analysiere Trendrichtung für jeden Timeframe
                tf1_bullish = self._has_confirmed_patterns(timeframe_patterns[tf1], ALL_BULLISH)
                tf1_bearish = self._has_confirmed_patterns(timeframe_patterns[tf1], ALL_BEARISH)
                tf2_bullish = self._has_confirmed_patterns(timeframe_patterns[tf2], ALL_BULLISH)
                tf2_bearish = self._has_confirmed_patterns(timeframe_patterns[tf2], ALL_BEARISH)

                # Konflikt: Kurzfristig bullisch, langfristig bearisch
                if tf1_bullish and tf2_bearish:
                    conflicts.append({
                        "type": "trend_conflict",
                        "timeframes": [tf1, tf2],
                        "description": f"Bullish {tf1} in Bearish {tf2} trend",
                        "severity": "moderate",  # Temporär, wird später aktualisiert
                        "recommendation": "Erhöhtes Risiko! Kurzfristige Trades nur mit strengen Stop-Loss betrachten"
                    })

                # Konflikt: Kurzfristig bearisch, langfristig bullisch
                if tf1_bearish and tf2_bullish:
                    conflicts.append({
                        "type": "trend_conflict",
                        "timeframes": [tf1, tf2],
                        "description": f"Bearish {tf1} in Bullish {tf2} trend",
                        "severity": "minor",  # Temporär, wird später aktualisiert
                        "recommendation": "Potentieller Rücksetzer - Kaufgelegenheit abwarten"
                    })

        return conflicts

    # Erkennt Konflikte zwischen S/R-Levels in Timeframes
    def detect_support_resistance_conflicts(self, timeframe_data, timeframe_patterns):
        """
        Identifiziert Konflikte zwischen Support/Resistance-Levels in verschiedenen Timeframes.
        """
        conflicts = []

        # Extrahiere S/R-Levels aus allen Timeframes
        sr_levels = self._extract_sr_levels(timeframe_data, timeframe_patterns)

        # Aktuelle Preise für jeden Timeframe
        current_prices = {tf: data['close'].iloc[-1] if not data.empty else None
                          for tf, data in timeframe_data.items()}

        # Vergleiche wichtige S/R-Levels zwischen Timeframes
        for i, tf1 in enumerate(self.timeframe_order):
            if tf1 not in sr_levels:
                continue

            for tf2 in self.timeframe_order[i + 1:]:
                if tf2 not in sr_levels:
                    continue

                # Suche nach Konflikten zwischen nahen S/R-Levels
                for level1 in sr_levels[tf1]:
                    for level2 in sr_levels[tf2]:
                        # Wenn ein kurzfristiger Support in der Nähe eines langfristigen Widerstands liegt
                        price_diff_pct = abs(level1["price"] - level2["price"]) / level1["price"]

                        if price_diff_pct < 0.03:  # 3% Toleranz
                            if level1["type"] != level2["type"]:
                                conflicts.append({
                                    "type": "sr_conflict",
                                    "timeframes": [tf1, tf2],
                                    "description": f"{level1['type'].title()} in {tf1} vs {level2['type'].title()} in {tf2}",
                                    "price_levels": [level1["price"], level2["price"]],
                                    "severity": "major",  # Temporär, wird später aktualisiert
                                    "recommendation": "Starke Preisreaktion in dieser Zone zu erwarten"
                                })

        return conflicts

    # Erkennt Konflikte in der Volumenbestätigung zwischen Timeframes
    def detect_volume_confirmation_conflicts(self, timeframe_data, timeframe_patterns):
        """
        Erkennt Konflikte in der Volumenbestätigung zwischen Timeframes.
        """
        conflicts = []

        # Überprüfe ob Volume-Daten vorhanden sind
        volume_available = all('volume' in data.columns for data in timeframe_data.values()
                               if not data.empty)

        if not volume_available:
            return conflicts

        # Für jeden Timeframe mit bestätigten Mustern
        for tf, patterns in timeframe_patterns.items():
            if tf not in timeframe_data or timeframe_data[tf].empty:
                continue

            # Finde bestätigte Muster
            confirmed_patterns = []
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if pattern.get('confirmed', False) and pattern.get('breakout_idx') is not None:
                        confirmed_patterns.append((pattern_type, pattern))

            # Überprüfe Volumenprofil für jedes bestätigte Muster
            for pattern_type, pattern in confirmed_patterns:
                breakout_idx = pattern.get('breakout_idx')

                # Volumen beim Ausbruch
                breakout_volume = timeframe_data[tf]['volume'].iloc[breakout_idx]
                avg_volume = timeframe_data[tf]['volume'].iloc[max(0, breakout_idx - 5):breakout_idx].mean()

                # Schwacher Ausbruch auf niedrigem Volumen
                if breakout_volume < avg_volume * 0.8:  # 20% unter Durchschnitt
                    # Suche nach Konflikten in höheren Timeframes
                    for higher_tf in self.timeframe_order[self.timeframe_order.index(tf) + 1:]:
                        if higher_tf in timeframe_patterns:
                            conflicts.append({
                                "type": "volume_conflict",
                                "timeframes": [tf],
                                "description": f"Schwache Volumenbestätigung für {pattern_type.replace('_', ' ')} in {tf}",
                                "severity": "minor",
                                "recommendation": "Auf Bestätigung in {higher_tf} warten"
                            })
                            break

        return conflicts

    # Erkennt Konflikte zwischen Marktphasen (Trend, Range, etc.) in Timeframes
    def detect_market_phase_conflicts(self, timeframe_data, timeframe_patterns):
        """
        Identifiziert Konflikte zwischen Marktphasen (Trend, Range, etc.) in verschiedenen Timeframes.
        """
        conflicts = []

        # Marktphasen für jeden Timeframe ermitteln
        market_phases = {}

        for tf, data in timeframe_data.items():
            if data.empty or len(data) < 20:
                continue

            # Einfacher Ansatz: Bestimme Trendrichtung mit linearer Regression
            x = np.arange(len(data))
            y = data['close'].values

            try:
                slope, _ = np.polyfit(x, y, 1)

                # Trendstärke mit Korrelation
                correlation = np.corrcoef(x, y)[0, 1]
                trend_strength = abs(correlation)

                # Marktphasen bestimmen
                if trend_strength > 0.7:
                    phase = "strong_uptrend" if slope > 0 else "strong_downtrend"
                elif trend_strength > 0.3:
                    phase = "weak_uptrend" if slope > 0 else "weak_downtrend"
                else:
                    phase = "sideways"

                market_phases[tf] = {
                    "phase": phase,
                    "strength": trend_strength
                }
            except:
                continue

        # Konflikte zwischen verschiedenen Marktphasen
        for i, tf1 in enumerate(self.timeframe_order):
            if tf1 not in market_phases:
                continue

            for tf2 in self.timeframe_order[i + 1:]:
                if tf2 not in market_phases:
                    continue

                # Starke Trendumkehr-Konflikte
                if ("uptrend" in market_phases[tf1]["phase"] and
                        "downtrend" in market_phases[tf2]["phase"]):

                    # Nur relevante Konflikte mit starken Trends
                    if (market_phases[tf1]["strength"] > 0.5 and
                            market_phases[tf2]["strength"] > 0.5):
                        conflicts.append({
                            "type": "market_phase_conflict",
                            "timeframes": [tf1, tf2],
                            "description": f"Uptrend in {tf1} vs Downtrend in {tf2}",
                            "severity": "moderate",
                            "recommendation": "Vorsicht bei langfristigen Positionierungen, kurzfristige Gegenbewegung möglich"
                        })

                # Downtrend im kurzfristigen Charts, aber starker Uptrend in höherem Timeframe
                elif ("downtrend" in market_phases[tf1]["phase"] and
                      "strong_uptrend" == market_phases[tf2]["phase"]):

                    conflicts.append({
                        "type": "market_phase_conflict",
                        "timeframes": [tf1, tf2],
                        "description": f"Rücksetzer in {tf1} während {tf2} Aufwärtstrend",
                        "severity": "minor",
                        "recommendation": "Mögliche Kaufgelegenheit beim Abschluss der Korrektur"
                    })

        return conflicts

    # ++++ Bewertun ++++
    # Bewertet die Schwere der Konflikte (aktuell auf Basis von 3 Faktoren)
    def _rate_conflict_severity(self, conflicts):
        """
        Bewertet die Schwere der Konflikte basierend auf verschiedenen Faktoren.
        """
        for conflict in conflicts:
            base_severity = conflict.get("severity", "minor")

            # Faktoren zur Anpassung der Schwere
            adjustment_factors = 0

            # Faktor 1: Stärke des Timeline-Gaps
            timeframes = conflict.get("timeframes", [])
            if len(timeframes) >= 2:
                tf_indices = [self.timeframe_order.index(tf) for tf in timeframes
                              if tf in self.timeframe_order]
                if max(tf_indices) - min(tf_indices) >= 2:
                    adjustment_factors += 1  # Größerer Abstand = schwerwiegender

            # Faktor 2: Konflikttyp
            if conflict.get("type") == "sr_conflict":
                adjustment_factors += 1  # S/R-Konflikte sind kritischer

            # Aktualisiere Schweregrad
            if base_severity == "minor" and adjustment_factors >= 1:
                conflict["severity"] = "moderate"
            elif base_severity == "moderate" and adjustment_factors >= 1:
                conflict["severity"] = "major"

    # ++++ Prüfung ++++
    # ++ Prüft, ob bestätigte Muster eines bestimmten Typs vorhanden sind
    def _has_confirmed_patterns(self, patterns, pattern_list):
        """
        Überprüft, ob bestätigte Muster eines bestimmten Typs vorhanden sind.
        """
        for pattern_type, pattern_list_items in patterns.items():
            if pattern_type in pattern_list:
                for pattern in pattern_list_items:
                    if pattern.get('confirmed', False):
                        return True
        return False

    # ++++ Extraktion ++++
    # ++ Extrahiert wichtige S/R-Levels aus Patterns und Preisdaten
    def _extract_sr_levels(self, timeframe_data, timeframe_patterns):
        """
        Extrahiert wichtige Support- und Resistance-Levels aus Patterns und Preisdaten.
        """
        sr_levels = {}

        for tf, patterns in timeframe_patterns.items():
            if tf not in timeframe_data or timeframe_data[tf].empty:
                continue

            sr_levels[tf] = []

            # S/R-Levels aus Mustern extrahieren
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    # Nacklinien aus Head & Shoulders / Double Tops/Bottoms
                    if 'neckline' in pattern:
                        level_type = "resistance" if pattern_type in ALL_BEARISH else "support"
                        sr_levels[tf].append({
                            "price": pattern['neckline'],
                            "type": level_type,
                            "source": pattern_type,
                            "strength": pattern.get('strength', 0.5)
                        })

                    # Resistance/Support-Levels aus Dreiecken
                    if 'resistance_level' in pattern:
                        sr_levels[tf].append({
                            "price": pattern['resistance_level'],
                            "type": "resistance",
                            "source": pattern_type,
                            "strength": pattern.get('strength', 0.5)
                        })

                    if 'support_level' in pattern:
                        sr_levels[tf].append({
                            "price": pattern['support_level'],
                            "type": "support",
                            "source": pattern_type,
                            "strength": pattern.get('strength', 0.5)
                        })

            # Zusätzliche Analyse für weitere S/R-Levels könnte hier hinzugefügt werden
            # z.B. Swing-Hochs/Tiefs, Fibonacci-Levels etc.

        return sr_levels

