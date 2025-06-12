# Pattern Pilot - Market Engine Dokumentation

## 1. Übersicht

Die `market_engine.py` ist das Herzstück des Pattern Pilot Systems. Sie bildet die zentrale Schnittstelle zwischen den Krypto-Börsen (Exchanges) und der Benutzeroberfläche, verarbeitet Marktdaten und implementiert die Pattern-Erkennung mittels TA-Lib.

**Hauptfunktionen:**
- Multi-Exchange-Anbindung über ccxt (130+ Börsen)
- Asynchrones Exchange-Loading via Threading
- OHLCV-Datenerfassung und -Verarbeitung
- Pattern-Erkennung mit TA-Lib (150+ technische Indikatoren)
- Dynamische Pattern-Filterung
- Marktdaten-Aggregation für UI-Status-Anzeigen

## 2. Architektur

Die `MarketEngine` Klasse implementiert einen Singleton-Ansatz und stellt alle Funktionen über eine zentrale Instanz bereit, die am Ende der Datei erstellt wird:

```python
# Singleton instance
market_engine = MarketEngine()
```

### Hauptkomponenten

```
MarketEngine
│
├── Exchange-Management
│   ├── _start_exchange_threads()
│   └── _load_exchange_thread()
│
├── Daten-Abruf
│   └── get_ohlcv()
│
├── Pattern-Detection
│   ├── detect_patterns()
│   └── filter_patterns()
│
├── Pattern-Helper
│   ├── _extract_pattern_signals()
│   ├── _detect_bb_squeeze()
│   ├── _detect_ma_crossover()
│   ├── _detect_rsi_signals()
│   ├── _detect_macd_crossover()
│   └── _detect_support_resistance()
│
└── Utility-Funktionen
    ├── get_available_symbols()
    ├── get_market_stats()
    └── get_exchange_info()
```

## 3. Exchange-Integration und API-Daten

### Exchange Initialisierung

Die Engine initialisiert Exchanges asynchron in separaten Threads, was einen schnelleren Start der UI ermöglicht:

```python
def _start_exchange_threads(self):
    """Startet Exchange-Loading parallel im Hintergrund"""
    configs = [
        ('binance', ccxt.binance, {'rateLimit': 1200}),
        ('coinbase', ccxt.coinbase, {'rateLimit': 1000}),
        ('kraken', ccxt.kraken, {'rateLimit': 3000}),
        ('bybit', ccxt.bybit, {'rateLimit': 1000}),
        ('okx', ccxt.okx, {'rateLimit': 1000}),
    ]
    
    # Thread für jeden Exchange starten
    for name, exchange_class, config in configs:
        thread = threading.Thread(
            target=self._load_exchange_thread,
            args=(name, exchange_class, config),
            daemon=True
        )
        thread.start()
```

### OHLCV-Daten Abruf

Die `get_ohlcv()` Methode ist für den Abruf von OHLCV-Daten (Open, High, Low, Close, Volume) zuständig und implementiert:

- Exchange-Auswahl und Auto-Routing
- Caching für Performance-Optimierung
- Automatisches Fallback bei Exchange-Fehlern

```python
def get_ohlcv(self, symbol: str, timeframe: str = '1d', 
              limit: int = 500, exchange: str = None) -> pd.DataFrame:
    """
    Holt OHLCV von besten verfügbaren Exchange
    
    Args:
        symbol (str): Trading-Pair (z.B. "BTC/USDT")
        timeframe (str): Zeitrahmen (z.B. "1d", "4h")
        limit (int): Anzahl der Candles
        exchange (str): Spezifischer Exchange oder None für Auto
        
    Returns:
        pd.DataFrame: DataFrame mit OHLCV-Daten
    """
```

Die Daten werden als pandas DataFrame mit folgenden Spalten zurückgegeben:
- `timestamp`: Unix-Timestamp in Millisekunden
- `open`: Eröffnungspreis
- `high`: Höchstpreis
- `low`: Tiefstpreis  
- `close`: Schlusskurs
- `volume`: Handelsvolumen
- `datetime`: Konvertierter Timestamp als pandas Datetime

## 4. Pattern-Erkennung

### Pattern-Typen

Die Pattern-Erkennung ist in zwei Hauptkategorien unterteilt:

1. **Candlestick-Patterns** (einzelne Kerzen-Formationen)
2. **Trend-Patterns** (mehrere Kerzen übergreifende Indikatoren)

### Detect Patterns Methode

Die `detect_patterns()` Methode ist das Herzstück der Pattern-Erkennung:

```python
def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Nutzt talib für 150+ professionelle Pattern
    
    Args:
        df: DataFrame mit OHLCV-Daten
        
    Returns:
        Dict mit erkannten Patterns und ihren Signalen
    """
```

Die Funktion extrahiert zunächst die benötigten Numpy-Arrays für TA-Lib:

```python
open_prices = df['open'].values
high_prices = df['high'].values  
low_prices = df['low'].values
close_prices = df['close'].values
volume = df['volume'].values
```

### Candlestick-Pattern Erkennung

Candlestick-Patterns werden über ein Dictionary mit TA-Lib-Funktionen definiert:

```python
candlestick_patterns = {
    'doji': talib.CDLDOJI,
    'hammer': talib.CDLHAMMER,
    # weitere Patterns...
}

for name, func in candlestick_patterns.items():
    result = func(open_prices, high_prices, low_prices, close_prices)
    signals = self._extract_pattern_signals(result, df, name)
    if signals:
        patterns[name] = signals
```

### Trend-Pattern Erkennung

Für komplexere Trend-Patterns werden spezielle Detektions-Methoden verwendet:

```python
# Bollinger Bands
bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices)
patterns['bollinger_squeeze'] = self._detect_bb_squeeze(
    close_prices, bb_upper, bb_lower, df
)

# Moving Average Crossovers
ma_fast = talib.SMA(close_prices, PATTERN_CONFIG['ma_crossover_fast'])
ma_slow = talib.SMA(close_prices, PATTERN_CONFIG['ma_crossover_slow'])
patterns['ma_crossover'] = self._detect_ma_crossover(
    ma_fast, ma_slow, df
)

# RSI
rsi = talib.RSI(close_prices, PATTERN_CONFIG['rsi_period'])
patterns['rsi_oversold'] = self._detect_rsi_signals(rsi, df, 'oversold')
patterns['rsi_overbought'] = self._detect_rsi_signals(rsi, df, 'overbought')

# MACD
macd, signal, hist = talib.MACD(close_prices)
patterns['macd_crossover'] = self._detect_macd_crossover(macd, signal, df)
```

### Pattern-Signal Format

Jedes erkannte Pattern wird in einem einheitlichen Format zurückgegeben:

```python
{
    'index': i,               # Index im DataFrame
    'datetime': datetime(...), # Zeitpunkt
    'price': 45678.90,        # Preis beim Signal
    'strength': 0.8,          # Signalstärke (0.0-1.0)
    'direction': 'bullish',   # Richtung (bullish/bearish/neutral/support/resistance)
    'pattern': 'hammer'       # Pattern-Typ
}
```

## 5. Einbinden neuer Patterns

### A) Candlestick-Pattern hinzufügen

Um ein neues Candlestick-Pattern aus TA-Lib hinzuzufügen:

1. **Schritt 1:** Öffne `market_engine.py` und suche nach dem `candlestick_patterns` Dictionary in der `detect_patterns()` Methode (ca. Zeile 103)

2. **Schritt 2:** Füge einen neuen Eintrag zum Dictionary hinzu:

```python
candlestick_patterns = {
    # Bestehende Patterns...
    'neues_pattern': talib.CDLNEWPATTERNNAME,  # Ersetze mit tatsächlichem TA-Lib Namen
}
```

3. **Schritt 3:** Öffne `config/settings.py` und füge das neue Pattern zur `candlestick_patterns` Liste hinzu (ca. Zeile 36):

```python
'candlestick_patterns': [
    # Bestehende Patterns...
    'neues_pattern',  # Neues Pattern hinzufügen
]
```

4. **Schritt 4:** Füge ein visuelles Styling für das neue Pattern hinzu (in `config/settings.py`, ca. Zeile 64):

```python
'pattern_styles': {
    # Bestehende Styles...
    'neues_pattern': {
        'symbol': 'circle',        # Plotly-Symbol (siehe 000_Plotly_Symbole.md)
        'color': '#00ff88',        # Hex-Farbe
        'size': 4,                 # Basis-Größe (wird mit Strength multipliziert)
        'emoji': '🔍'              # Emoji für UI-Anzeige
    },
}
```

### B) Benutzerdefiniertes Trend-Pattern hinzufügen

Für komplexere Trend-Patterns, die spezielle Logik benötigen:

1. **Schritt 1:** Erstelle eine neue Helper-Methode in der `MarketEngine` Klasse:

```python
def _detect_my_custom_pattern(self, df: pd.DataFrame) -> List[Dict]:
    """Custom Pattern Detection Logic"""
    signals = []
    
    # Implementiere deine Pattern-Logik hier
    # Beispiel: Moving Average Ribbon
    ma_5 = talib.SMA(df['close'].values, timeperiod=5)
    ma_10 = talib.SMA(df['close'].values, timeperiod=10)
    ma_20 = talib.SMA(df['close'].values, timeperiod=20)
    
    for i in range(1, len(df)):
        # Definiere Bedingungen für dein Pattern
        if (ma_5[i] > ma_10[i] > ma_20[i] and
            ma_5[i-1] <= ma_10[i-1]):
            
            signals.append({
                'index': i,
                'datetime': df['datetime'].iloc[i],
                'price': df['close'].iloc[i],
                'strength': 0.75,  # Pattern-Stärke definieren
                'direction': 'bullish',  # Richtung definieren
                'pattern': 'custom_ma_ribbon'  # Name deines Patterns
            })
    
    return signals
```

2. **Schritt 2:** Füge den Aufruf deiner neuen Methode in `detect_patterns()` hinzu:

```python
# In der detect_patterns() Methode
patterns['custom_ma_ribbon'] = self._detect_my_custom_pattern(df)
```

3. **Schritt 3:** Füge dein Pattern zur Liste in `config/settings.py` hinzu und definiere das Styling wie oben beschrieben.

### C) TA-Lib-Konfiguration anpassen

Um die Parameter bestehender TA-Lib-Funktionen anzupassen:

1. **Schritt 1:** Öffne `config/settings.py` und finde oder erstelle die entsprechenden Parameter im `PATTERN_CONFIG` Dictionary:

```python
'PATTERN_CONFIG': {
    # Bestehende Konfiguration...
    'ma_crossover_fast': 20,  # Jetzt 20 Perioden
    'ma_crossover_slow': 50,  # Jetzt 50 Perioden
    'custom_pattern_param': 15,  # Parameter für dein neues Pattern
}
```

2. **Schritt 2:** Verwende diese Parameter in deiner Pattern-Logik:

```python
# In market_engine.py
ma_fast = talib.SMA(close_prices, PATTERN_CONFIG['ma_crossover_fast'])
ma_slow = talib.SMA(close_prices, PATTERN_CONFIG['ma_crossover_slow'])
# oder für dein benutzerdefiniertes Pattern
custom_param = PATTERN_CONFIG['custom_pattern_param']
```

## 6. Pattern-Filterung und Verarbeitung

### Filter Patterns Methode

Die `filter_patterns()` Methode ermöglicht dynamisches Filtern von Patterns basierend auf:
- Pattern-Typen
- Signal-Richtung (bullish, bearish, etc.)
- Minimale Signalstärke

```python
def filter_patterns(self, patterns: Dict[str, List],
                   min_strength: float = 0.0,
                   directions: List[str] = None,
                   pattern_types: List[str] = None) -> Dict[str, List]:
    """
    Dynamischer Pattern-Filter
    
    Args:
        patterns: Original Patterns aus detect_patterns()
        min_strength: Minimale Signalstärke (0.0-1.0)
        directions: Liste von Richtungen ('bullish', 'bearish', 'neutral', etc.)
        pattern_types: Spezifische Pattern-Typen
        
    Returns:
        Gefilterte Patterns
    """
```

## 7. Utility-Funktionen

### Symbol-Liste abrufen

```python
def get_available_symbols(self, exchange: str = 'binance') -> List[str]:
    """Gibt Liste verfügbarer Trading-Pairs zurück"""
```

### Marktstatistiken abrufen

```python
def get_market_stats(self) -> Dict[str, Any]:
    """Gibt globale Marktdaten für Status-Bar zurück"""
```

### Exchange-Informationen abrufen

```python
def get_exchange_info(self) -> Dict[str, Any]:
    """Gibt Status und Info zu allen Exchanges zurück"""
```

## 8. Best Practices und Tipps

### Performance-Optimierung

1. **Caching nutzen**: Die Engine implementiert bereits ein Memory-Cache-System, das API-Calls für 5 Minuten speichert:

```python
if cache_key in self.cache:
    cached_data, timestamp = self.cache[cache_key]
    if time.time() - timestamp < 300:  # 5min cache
        return cached_data
```

2. **Batch-Verarbeitung**: Für große Datenmengen Pattern-Erkennung in Batches durchführen.

3. **Asynchrone Threads**: Die Exchange-Initialisierung erfolgt bereits asynchron, was die UI-Startzeit deutlich verbessert.

### Exchange-Failover Strategie

Die Engine implementiert ein automatisches Failover zwischen Exchanges:

```python
exchange_order = ['binance', 'coinbase', 'kraken', 'bybit', 'okx']
for ex_name in exchange_order:
    # Versuche Daten von diesem Exchange zu holen
    # Bei Fehler: Weiter zum nächsten Exchange
```

Um die Failover-Priorität anzupassen, ändere die Reihenfolge im `exchange_order` Array.

### Debug-Tipps

Bei Problemen mit der Pattern-Erkennung:

1. Prüfe die zurückgegebenen Numpy-Arrays von TA-Lib-Funktionen auf `nan`-Werte.
2. Stelle sicher, dass die DataFrame-Indizes konsistent sind.
3. Beachte, dass einige TA-Lib-Funktionen am Anfang des Arrays `nan`-Werte zurückgeben, bis genügend Datenpunkte für die Berechnung vorhanden sind.

## 9. Häufig genutzte TA-Lib Funktionen

### Indikatoren

```python
# Gleitende Durchschnitte
SMA = talib.SMA(close_prices, timeperiod=20)     # Simple Moving Average
EMA = talib.EMA(close_prices, timeperiod=20)     # Exponential Moving Average
WMA = talib.WMA(close_prices, timeperiod=20)     # Weighted Moving Average

# Oszillatoren
RSI = talib.RSI(close_prices, timeperiod=14)     # Relative Strength Index
MACD, MACD_SIGNAL, MACD_HIST = talib.MACD(       # Moving Average Convergence/Divergence
    close_prices, 
    fastperiod=12, 
    slowperiod=26, 
    signalperiod=9
)
STOCH_K, STOCH_D = talib.STOCH(                  # Stochastic Oscillator
    high_prices, 
    low_prices, 
    close_prices
)

# Volatilitäts-Indikatoren
UPPER, MIDDLE, LOWER = talib.BBANDS(             # Bollinger Bands
    close_prices, 
    timeperiod=20, 
    nbdevup=2, 
    nbdevdn=2
)
ATR = talib.ATR(                                 # Average True Range
    high_prices, 
    low_prices, 
    close_prices, 
    timeperiod=14
)
```

### Candlestick-Patterns

TA-Lib bietet 61 verschiedene Candlestick-Pattern-Funktionen, hier sind einige häufig genutzte:

```python
talib.CDLDOJI               # Doji
talib.CDLHAMMER             # Hammer
talib.CDLENGULFING          # Engulfing Pattern
talib.CDLMORNINGSTAR        # Morning Star
talib.CDLEVENINGSTAR        # Evening Star
talib.CDL3WHITESOLDIERS     # Three White Soldiers
talib.CDL3BLACKCROWS        # Three Black Crows
talib.CDLHARAMI             # Harami Pattern
talib.CDLHANGINGMAN         # Hanging Man
talib.CDLSHOOTINGSTAR       # Shooting Star
```

Die vollständige Liste aller 61 Candlestick-Patterns von TA-Lib findest du in der [offiziellen TA-Lib Dokumentation](https://ta-lib.org/function.html).

## 10. Häufige Fehler und Lösungen

### Exchange Connection Probleme

**Problem:** Exchanges werden nicht geladen oder geben Fehler zurück.

**Lösung:**
- Rate-Limiting überprüfen (zu viele Anfragen in kurzer Zeit)
- Netzwerkverbindung prüfen
- ccxt-Version aktualisieren (`pip install ccxt --upgrade`)

### TA-Lib Installation Probleme

**Problem:** TA-Lib kann nicht installiert werden oder gibt Fehler bei der Installation zurück.

**Lösung:**
- Windows: Verwende vorkompilierte Wheels: `pip install ta-lib-binary`
- Linux: Installiere die C-Bibliothek: `apt-get install ta-lib`
- Alternative: Verwende `market_engine_lite.py`, die ohne TA-Lib auskommt

### Memory-Leaks bei langen Sessions

**Problem:** Bei längeren Sessions kann es zu Memory-Leaks kommen.

**Lösung:**
- Cache-Größe begrenzen
- Regelmäßig nicht mehr benötigte DataFrames explizit freigeben
- Speichernutzung überwachen und bei Bedarf Engine neu initialisieren
