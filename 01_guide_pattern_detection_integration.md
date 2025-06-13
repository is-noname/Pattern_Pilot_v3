# Integration eigener Pattern-Erkennungsfunktionen

Diese Dokumentation beschreibt, wie du eigene Pattern-Erkennungsfunktionen erstellst, die mit der existierenden TA-Lib-Infrastruktur und `_extract_pattern_signals`-Methode kompatibel sind.

## 1. Anforderungen an die Ausgabe

Jede eigene Pattern-Erkennungsfunktion muss folgende Anforderungen erfüllen:

- **Rückgabetyp:** `numpy.ndarray` (1-dimensionales Array)
- **Länge:** Muss exakt der Länge des Dataframes entsprechen (`len(df)`)
- **Werte:**
  - `0` = Kein Pattern erkannt
  - `100` = Bullisches Pattern erkannt
  - `-100` = Bärisches Pattern erkannt
  - Andere Werte zwischen -100 und 100 können für unterschiedliche Stärkegrade verwendet werden

Diese Anforderungen stellen sicher, dass deine Funktion mit der `_extract_pattern_signals`-Methode kompatibel ist, die die numerischen Werte in ein strukturiertes Format umwandelt.

## 2. Struktur einer eigenen Pattern-Erkennungsfunktion

```python
def _detect_custom_pattern(self, df: pd.DataFrame) -> np.ndarray:
    """
    Erkennt eigenes Pattern im DataFrame
    
    Args:
        df: DataFrame mit OHLCV-Daten
        
    Returns:
        numpy.ndarray: Array mit Werten 0, 100, -100
    """
    # Initialisiere Array mit Nullen (kein Pattern)
    result = np.zeros(len(df))
    
    # Iteriere durch mögliche Pattern-Positionen
    for i in range(min_lookback, len(df) - forward_window):
        # Implementiere deine Pattern-Erkennungslogik
        # ...
        
        # Wenn bullisches Pattern erkannt:
        if bullish_pattern_condition:
            result[i] = 100
        
        # Wenn bärisches Pattern erkannt:
        elif bearish_pattern_condition:
            result[i] = -100
    
    return result
```

## 3. Integration in die `detect_patterns`-Methode

```python
def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
    """Pattern Detection Hauptmethode"""
    if df.empty or len(df) < 10:
        return {}
    
    patterns = {}
    
    # TA-Lib Candlestick Patterns
    # ...vorhandener Code...
    
    # Eigene Pattern-Erkennung hinzufügen
    try:
        # 1. Pattern-Erkennungsfunktion aufrufen
        custom_result = self._detect_custom_pattern(df)
        
        # 2. Ergebnis in das Standard-Format umwandeln
        signals = self._extract_pattern_signals(custom_result, df, "custom_pattern")
        
        # 3. Wenn Signale gefunden wurden, zum patterns-Dictionary hinzufügen
        if signals:
            patterns["custom_pattern"] = signals
    except Exception as e:
        print(f"⚠️ Custom pattern detection failed: {e}")
    
    return patterns
```

## 4. Beispiel: Inverse Head & Shoulders Pattern

```python
def _detect_inverse_head_shoulders(self, df: pd.DataFrame) -> np.ndarray:
    """Erkennt Inverse Head & Shoulders Pattern"""
    result = np.zeros(len(df))
    
    # Mindestanforderungen
    min_length = 15
    
    for i in range(10, len(df) - 30):
        # Suche nach drei Tiefs (linke Schulter, Kopf, rechte Schulter)
        # Nur ein vereinfachtes Beispiel:
        if i+10 < len(df) and i+20 < len(df):
            left_shoulder = df['low'].iloc[i]
            head = df['low'].iloc[i+10]
            right_shoulder = df['low'].iloc[i+20]
            
            # Pattern-Bedingungen prüfen:
            # 1. Kopf muss tiefer sein als beide Schultern
            # 2. Schultern sollten auf ähnlichem Niveau sein
            if (head < left_shoulder and 
                head < right_shoulder and
                abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                
                # Signalposition setzen (typischerweise am Ende des Patterns)
                result[i+20] = 100  # Bullishes Signal
    
    return result
```

## 5. Wichtige Hinweise

- **Performance:** Pattern-Erkennung kann rechenintensiv sein. Optimiere deine Funktionen, um unnötige Schleifen zu vermeiden.
- **Lookback-Periode:** Stelle sicher, dass deine Funktion nicht an den Anfang des DataFrames greift, wo keine ausreichenden Daten für die Erkennung vorhanden sind.
- **Falsche Positive:** Verwende strenge Bedingungen, um die Anzahl falscher Signale zu reduzieren.
- **Parametrisierung:** Überlege, ob du die Pattern-Parameter konfigurierbar machen möchtest (z.B. über `config/settings.py`).
- **Visualisierung:** Füge die neuen Patterns zur Visualisierung in `config/settings.py` unter `pattern_styles` hinzu.

## 6. Anpassung der Ausgabe für unterschiedliche Signalstärken

Du kannst auch verschiedene Signalstärken zurückgeben, indem du Werte zwischen -100 und 100 verwendest:

```python
# Sehr starkes bullisches Signal
result[i] = 100  

# Mittelstarkes bullisches Signal
result[i] = 75   

# Schwaches bullisches Signal
result[i] = 50   

# Schwaches bärisches Signal
result[i] = -50  

# Mittelstarkes bärisches Signal
result[i] = -75  

# Sehr starkes bärisches Signal
result[i] = -100 
```

Die `_extract_pattern_signals`-Methode normalisiert diese Werte automatisch auf einen Bereich von 0.0 bis 1.0 für die `strength`-Eigenschaft.
