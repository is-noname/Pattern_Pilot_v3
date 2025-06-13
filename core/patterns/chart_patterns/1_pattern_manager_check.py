# standalone_pattern_manager_test.py
# Diese Datei sollte im Hauptverzeichnis des Projekts liegen, nicht im patterns-Ordner

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Sicherstellen, dass wir das richtige Verzeichnis im Pfad haben
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


# Testdaten erstellen
def create_test_data():
    # Einfaches Doppel-Bottom-Muster erzeugen
    days = 100
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    dates.reverse()

    # Basispreis mit leichter Aufwärtstendenz
    close = [100 + i * 0.5 + np.random.normal(0, 2) for i in range(days)]

    # Doppel-Bottom einfügen (bei ca. 1/3 und 2/3)
    for i in range(30, 40):
        close[i] -= 15 - abs(i - 35) * 2  # Erstes Bottom

    for i in range(60, 70):
        close[i] -= 15 - abs(i - 65) * 2  # Zweites Bottom

    # OHLCV-Daten erstellen
    high = [c + np.random.uniform(0.5, 3) for c in close]
    low = [c - np.random.uniform(0.5, 3) for c in close]
    open_price = [c + np.random.uniform(-2, 2) for c in close]
    volume = [1000 + np.random.uniform(0, 500) for _ in range(days)]

    # DataFrame erstellen
    df = pd.DataFrame({
        'date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    return df


# Nur das Minimum importieren, was wir brauchen
from patterns.double_patterns import detect_double_bottom


# Simplified Pattern Manager Class für Test
class TestPatternManager:
    def __init__(self):
        self.detectors = {"double_bottom": detect_double_bottom}
        self._cache = {}

    def detect_patterns(self, df, timeframe="1d", use_cache=True):
        # Cache-Key erstellen
        if use_cache:
            cache_key = f"{hash(df.to_json())}-{timeframe}"
            if cache_key in self._cache:
                return self._cache[cache_key]

        results = {}
        for pattern_name, detector_func in self.detectors.items():
            try:
                patterns = detector_func(df, None, timeframe)
                results[pattern_name] = patterns
            except Exception as e:
                print(f"Error with {pattern_name}: {e}")
                results[pattern_name] = []

        if use_cache:
            self._cache[cache_key] = results

        return results

    def clear_cache(self):
        self._cache = {}
        print("Cache cleared")


# Test ausführen
def main():
    print("🚀 Test Pattern Manager")

    # Test-Daten erstellen
    df = create_test_data()
    print(f"✅ Test-Daten erstellt: {len(df)} Datenpunkte")

    # Pattern Manager initialisieren
    manager = TestPatternManager()
    print("✅ Test Manager initialisiert")

    # Patterns erkennen
    print("\n🔍 Pattern-Erkennung:")
    patterns = manager.detect_patterns(df)

    # Ergebnisse prüfen
    if patterns and patterns.get("double_bottom"):
        print(f"✅ Double Bottom gefunden: {len(patterns['double_bottom'])} Instanzen")
        # Details ausgeben
        for i, pattern in enumerate(patterns["double_bottom"]):
            print(f"\nPattern #{i + 1} Details:")
            for key, value in pattern.items():
                print(f"  {key}: {value}")
    else:
        print("❌ Keine Double Bottoms erkannt")

    # Cache-Test
    print("\n🔍 Pattern-Erkennung mit Cache (sollte schneller sein):")
    import time
    start = time.time()
    patterns_cached = manager.detect_patterns(df)
    cached_time = time.time() - start
    print(f"⏱️ Zeit mit Cache: {cached_time:.6f}s")

    # Cache löschen und neu erkennen
    manager.clear_cache()
    start = time.time()
    patterns_no_cache = manager.detect_patterns(df)
    no_cache_time = time.time() - start
    print(f"⏱️ Zeit ohne Cache: {no_cache_time:.6f}s")
    print(f"🚀 Beschleunigung: {no_cache_time / cached_time:.2f}x")


if __name__ == "__main__":
    main()