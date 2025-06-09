# Implementierungsplan für Pattern-Integration

## Überblick
Dieses Dokument beschreibt die Implementierungsstrategie zur Integration fortschrittlicher technischer Analysemuster in Pattern Pilot. Der Fokus liegt auf Mustern, die nicht direkt über TA-Lib verfügbar sind und eine eigene Implementierung erfordern.

## 1. Modulstruktur
- Erstelle Unterordner `core/patterns/` für bessere Organisation
- Individuelle Pattern-Dateien für bessere Wartbarkeit:
  - `patterns/ichimoku.py`
  - `patterns/double_bottom.py`
  - `patterns/head_shoulders.py`
  - `patterns/trend_channels.py`
  - `patterns/triangles.py`
  - `patterns/rectangles.py`
- Gemeinsame Hilfsfunktionen in `patterns/utils.py`

## 2. Integration in Market Engine
```python
# In der detect_patterns() Methode:
# Füge diese Zeilen hinzu, um neue Muster zu integrieren
patterns['ichimoku_cross'] = self._detect_ichimoku_cross(df)
patterns['double_bottom'] = self._detect_double_bottom(df)
patterns['triple_bottom'] = self._detect_triple_bottom(df)
patterns['rising_triangle'] = self._detect_rising_triangle(df)
patterns['head_shoulders'] = self._detect_head_shoulders(df)
patterns['inv_head_shoulders'] = self._detect_inv_head_shoulders(df)
patterns['trend_channel'] = self._detect_trend_channel(df)
patterns['rectangle'] = self._detect_rectangle(df)
```

Jede Erkennungsmethode sollte eine einheitliche Signatur haben:
```python
def _detect_pattern_name(self, df: pd.DataFrame) -> List[Dict]:
    """Pattern-Erkennungsimplementierung"""
    signals = []
    # Implementierungslogik
    return signals
```

## 3. Pattern-Styling Konfiguration
Erweitere `config/settings.py` mit visuellen Stilen für jedes Muster:

```python
'pattern_styles': {
    # Bestehende Muster...
    'ichimoku_cross': {'symbol': 'star-triangle-up', 'color': '#00d4ff', 'size': 5, 'emoji': '🌊'},
    'double_bottom': {'symbol': 'circle-open', 'color': '#00ff77', 'size': 5, 'emoji': 'W'},
    'head_shoulders': {'symbol': 'diamond-tall', 'color': '#ff3388', 'size': 5, 'emoji': '👑'},
    # Füge restliche Muster hinzu...
}
```

## 4. Timeframe-Bewusste Implementierung
- Füge Timeframe-Parameter zu Pattern-Erkennungsfunktionen hinzu
- Implementiere Signalstärke-Multiplikatoren basierend auf Timeframe:
  - 4h: Basisstärke
  - 1d: 1,5x Multiplikator
  - 1w: 2,5x Multiplikator
  - 1M: 4x Multiplikator
- Erstelle zusammengesetzte Signale, die Muster über mehrere Timeframes erkennen

## 5. Implementierungspriorität
1. **Phase 1 (Hohe Auswirkung):**
   - Ichimoku Cloud Cross
   - Doppelboden (W-Muster)
   - Schulter-Kopf-Schulter / Inverse SKS

2. **Phase 2 (Mittlere Auswirkung):**
   - Steigendes Dreieck
   - Rechteck-Muster
   - Trendkanäle

3. **Phase 3 (Verfeinerung):**
   - Dreifachboden
   - Zusätzliche spezialisierte Muster
   - Verbesserung der Signalqualität

## 6. UI-Erweiterungen
- Füge Dropdown-Filter für Pattern-Typen in der UI hinzu
- Integriere Erfolgswahrscheinlichkeiten in Hover-Tooltips
- Erstelle ein dediziertes Pattern-Übersichtspanel mit:
  - Häufigkeit der Pattern-Typen
  - Historische Erfolgsraten
  - Timeframe-Verteilung

## 7. Dokumentation
- Erstelle einen Pattern-Referenzleitfaden mit:
  - Visuellen Beispielen für jedes Muster
  - Erwartete Erfolgsraten nach Timeframe
  - Häufige Fehlauslöser und wie man sie vermeidet
  - Beste Bestätigungsindikatoren
- Füge Inline-Code-Dokumentation für alle Pattern-Erkennungsalgorithmen hinzu

## 8. Testansatz
- Erstelle pattern-spezifische Backtesting-Mechanismen
- Vergleiche Erkennungsgenauigkeit mit manueller Identifikation
- Optimiere Parameter für maximale True-Positive-Rate
