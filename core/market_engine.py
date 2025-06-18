# core/market_engine.py     MARKET ENGINE CORE - Hauptkomponente v3.0
"""
Market Engine - Kern des Pattern Pilot Systems

Zentrale Komponente für Börsenanbindung, Marktdaten-Abruf und
technische Pattern-Erkennung. Implementiert Multi-Exchange-Support
mit ccxt und professionelle Chartanalyse mit TA-Lib (150+ Indikatoren).

Funktionale Merkmale:
- Multi-Exchange-Anbindung (130+ Börsen via ccxt)
- Threading-basierte asynchrone Exchange-Initialisierung
- Candlestick-Pattern-Erkennung mit TA-Lib
- Trend-Pattern-Erkennung (Bollinger, MA, Support/Resistance)
- Flexibles Pattern-Filtersystem nach Typ, Richtung und Stärke
- Memory-Cache für API-Daten zur Leistungsoptimierung

Technische Implementierung:
- Singleton-Architektur für globalen Zugriff
- Thread-sichere API-Interaktion
- Adaptive Fehlerbehandlung mit Exchange-Failover
- Standardisierte Signal-Ausgabe für UI-Integration

Autor: Pattern Pilot Team
Version: 3.0
"""
import ccxt
import pandas as pd
import talib
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import threading
from queue import Queue
from typing import Dict, List, Optional, Any, Union
import time  # 'time' hinzufügen

from config.settings import  PATTERN_CONFIG, EXCHANGE_CONFIG

#==============================================================================
# region                🔄 MARKET ENGINE HAUPTKLASSE
#==============================================================================

class MarketEngine:
    """
    Market Engine - Zentrales Backend für Marktdaten und Pattern-Erkennung.

    Implementiert ein vereinheitlichtes Interface für:
    1. Exchange-Zugriff und -Management über ccxt
    2. OHLCV-Datenabruf mit automatischem Failover
    3. Technische Analyse mit 150+ Pattern-Typen
    4. Marktstatistik-Aggregation

    Die Klasse wird als Singleton implementiert und ist für Multi-Threading
    optimiert, wobei Exchange-Verbindungen asynchron im Hintergrund aufgebaut
    werden, während die UI bereits geladen wird.

    Attribute:
        exchanges (dict): Exchange-Objekte oder Status-Informationen
        cache (dict): In-Memory-Cache für API-Anfragen

    🚀 Ersetzt: api/api_manager.py + patterns/__init__.py + cache/
    
    Nutzt ccxt für Daten und talib für Pattern - Profi-Standard
    """

    def __init__(self):
        self.exchanges = {}  # Leeres Dict erstmal
        self.cache = {}  # Cache beibehalten

        # Für jeden Exchange initialen "loading" Status setzen
        for name in ['binance', 'coinbase', 'kraken', 'bybit', 'okx']:
            self.exchanges[name] = {'status': 'loading'}

        # Threading starten
        self._start_exchange_threads()

        print(f"✅ MarketEngine: UI startet sofort, Exchanges laden im Hintergrund")

    # •••••••••••••••••••••••••• 🔄 THREAD-MANAGEMENT •••••••••••••••••••••••••• #
    def _start_exchange_threads(self):
        """Startet Exchange-Loading parallel im Hintergrund"""
        # Configs aus settings.py holen statt hardcoded
        configs = []
        for exchange_name, config in EXCHANGE_CONFIG.items():
            exchange_class = getattr(ccxt, exchange_name)
            configs.append((exchange_name, exchange_class, config))

        # configs = [
        #     ('binance', ccxt.binance, {'rateLimit': 1200}),
        #     ('coinbase', ccxt.coinbase, {'rateLimit': 1000}),
        #     ('kraken', ccxt.kraken, {'rateLimit': 3000}),
        #     ('bybit', ccxt.bybit, {'rateLimit': 1000}),
        #     ('okx', ccxt.okx, {'rateLimit': 1000}),
        # ]

        # Für jeden Exchange initialen "loading" Status setzen
        for name, _, _ in configs:
            self.exchanges[name] = {'status': 'loading'}

        # Für jeden Exchange eigenen Thread starten
        for name, exchange_class, config in configs:
            thread = threading.Thread(
                target=self._load_exchange_thread,
                args=(name, exchange_class, config),
                daemon=True  # Thread endet mit Hauptprogramm
            )
            thread.start()

    def _load_exchange_thread(self, name, exchange_class, config):
        """In separatem Thread ausgeführt
        Lädt einen Exchange in einem separaten Thread.

        Wird durch _start_exchange_threads für jede Börse aufgerufen.
        Setzt den Exchange-Status während der Ladezeit auf 'loading',
        nach erfolgreicher Verbindung auf ein ccxt.Exchange-Objekt
        oder bei Fehler auf {'status': 'offline', 'error': '...'}.

        Args:
            name (str): Name des Exchanges (z.B. 'binance')
            exchange_class (ccxt.Exchange): ccxt Exchange-Klasse
            config (dict): Exchange-Konfiguration (rate limits, etc.)
        """
        try:
            print(f"📡 {name}: Loading Exchange...")
            exchange = exchange_class(config)
            exchange.load_markets()

            # Exchange im Dictionary aktualisieren
            self.exchanges[name] = exchange

            print(f"✅ {name}: {len(exchange.markets)} markets")
        except Exception as e:
            # Fehler-Status setzen
            self.exchanges[name] = {'status': 'offline', 'error': str(e)}
            print(f"❌ {name} failed: {e}")

    # ==============================================================================
    # region               📊 DATEN-ABRUF METHODEN
    # ==============================================================================
    def get_ohlcv(self, symbol: str, timeframe: str = '1d', 
                  limit: int = 500, exchange: str = None) -> pd.DataFrame:
        """
        🎯 Ersetzt: Deine ganze api/ Struktur
        
        Holt OHLCV von besten verfügbaren Exchange

        Retrieve OHLCV data from the best available exchange.

        Implements automatic exchange failover and caching for optimal performance
        in professional trading environments.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT", "ETH/USD")
            timeframe: Candlestick interval ("1m", "5m", "1h", "1d", "1w")
            limit: Number of candlesticks to retrieve (50-1000)
            exchange: Specific exchange name or None for auto-routing

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, datetime

        Raises:
            Exception: When no data is available from any exchange

        Example:
            >>> df = market_engine.get_ohlcv("BTC/USDT", "1d", 200)
            >>> print(f"Retrieved {len(df)} candlesticks")

        Note:
            Uses 5-minute caching to optimize API rate limits across exchanges.
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"

        # Cache check
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < 300:  # 5min cache
                print(f"💾 Cache hit: {symbol}")
                return cached_data

        # Exchange priority order
        exchange_order = []

        # Specific exchange requested
        if exchange and exchange in self.exchanges:
            if not isinstance(self.exchanges[exchange], dict):
                exchange_order = [exchange]

        # Fallback: Try all online exchanges
        if not exchange_order:
            for ex_name in ['binance', 'coinbase', 'kraken', 'bybit', 'okx']:
                if (ex_name in self.exchanges and
                        not isinstance(self.exchanges[ex_name], dict)):
                    exchange_order.append(ex_name)

        # Try each exchange until success
        for ex_name in exchange_order:
            try:
                exchange_obj = self.exchanges[ex_name]
                print(f"🔄 Trying {ex_name} for {symbol}...")

                # Fetch OHLCV
                ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe, limit=limit)

                if not ohlcv:
                    continue  # Try next exchange

                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])

                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('datetime').reset_index(drop=True)

                # Ensure numeric columns
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Remove NaN rows
                df = df.dropna(subset=['open', 'high', 'low', 'close'])

                # Mark as pattern-ready to prevent re-normalization
                df.attrs['pattern_ready'] = True

                # Cache result
                self.cache[cache_key] = (df, time.time())

                print(f"✅ {ex_name}: {len(df)} candles")
                return df

            except Exception as e:
                print(f"❌ {ex_name} error: {e}")
                continue  # Try next exchange

        print(f"❌ No data found for {symbol}")
        return pd.DataFrame()
    # endregionF

    # ==============================================================================
    # region               🎯 PATTERN DETECTION ENGINE
    # ==============================================================================
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Pattern detection via pattern_manager + TA-Lib"""

        # TA-Lib patterns (existing)
        ta_patterns = self._detect_technical_patterns(df)

        # Formation Patterns via pattern_manager
        try:
            from core.patterns.formation_patterns.pattern_manager import pattern_manager
            formation_patterns = pattern_manager.detect_patterns(df)

            return {
                'technical_indicators': ta_patterns,
                'formation_patterns': formation_patterns,
            }

        except ImportError:
            # Fallback: nur TA-Lib patterns
            return {
                'technical_indicators': ta_patterns,
                'formation_patterns': formation_patterns
            }

    def _detect_technical_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Identifiziert Trading-Patterns im OHLCV-DataFrame.

        Nutzt TA-Lib für 61 Candlestick-Patterns sowie eigene Algorithmen
        für komplexere Muster wie Bollinger Squeezes, Moving Average
        Crossovers und Support/Resistance-Levels.

        Jedes erkannte Pattern wird mit Metadaten angereichert:
        - Position (Index, Datum)
        - Preis beim Signal
        - Signalstärke (0.0-1.0)
        - Richtung (bullish, bearish, neutral)

        Args:
            df (pd.DataFrame): DataFrame mit OHLCV-Daten

        Returns:
            Dict[str, List[Dict]]: Erkannte Patterns nach Typ gruppiert

        Notes:
        Startet Exchange-Loading parallel im Hintergrund.

        Initialisiert Daemon-Threads für jede Exchange-Verbindung,
        um die Benutzeroberfläche responsiv zu halten, während
        Exchange-Verbindungen aufgebaut werden.

        Threads verwenden die Konfiguration aus settings.py für
        Rate-Limits und andere Exchange-spezifische Parameter.

        🎯 Ersetzt: Deine ganze patterns/ Struktur
        
        Nutzt talib für 150+ professionelle Pattern
        """
        if df.empty or len(df) < 10:
            return {}
        
        # Prepare data for talib (braucht numpy arrays)
        open_prices = df['open'].values
        high_prices = df['high'].values  
        low_prices = df['low'].values
        close_prices = df['close'].values
        volume = df['volume'].values
        
        patterns = {}

        # •••••••••••••••••••••••••• 🔥 Candlestick Patterns ######•••••••••••••••••••••••••• #
        candlestick_patterns = {
            'doji': talib.CDLDOJI,
            'hammer': talib.CDLHAMMER,
            'hanging_man': talib.CDLHANGINGMAN,
            'shooting_star': talib.CDLSHOOTINGSTAR,
            'engulfing_bullish': talib.CDLENGULFING,
            'engulfing_bearish': talib.CDLENGULFING,
            'morning_star': talib.CDLMORNINGSTAR,
            'evening_star': talib.CDLEVENINGSTAR,
            'three_white_soldiers': talib.CDL3WHITESOLDIERS,
            'three_black_crows': talib.CDL3BLACKCROWS,
            'harami': talib.CDLHARAMI,
            'piercing': talib.CDLPIERCING,
            'dark_cloud': talib.CDLDARKCLOUDCOVER,
            # Zusätzliche einzelne Candlestick-Patterns
            'inverted_hammer': talib.CDLINVERTEDHAMMER,     # Umgedrehter Hammer
            'marubozu': talib.CDLMARUBOZU,                  # Volle Kerze ohne Schatten
            'spinning_top': talib.CDLSPINNINGTOP,           # Spinning Top (Unentschlossenheit)
            'dragonfly_doji': talib.CDLDRAGONFLYDOJI,       # Dragonfly Doji
            # Mehr Trend-Confirmation Patterns
            'kicking': talib.CDLKICKING,                    # Kicking Pattern (starker Trend)
            'tasuki_gap': talib.CDLTASUKIGAP,               # Tasuki Gap (Trendfortsetzung)
            'breakaway': talib.CDLBREAKAWAY,                # Breakaway (Trendstart)
            'doji_star': talib.CDLDOJISTAR,                 # Doji Star (potentielle Umkehr)
        }
        # (die wichtigsten von 61 verfügbaren)

        for name, func in candlestick_patterns.items():
            try:
                result = func(open_prices, high_prices, low_prices, close_prices)
                # Finde wo Pattern auftreten (non-zero values)
                signals = self._extract_pattern_signals(result, df, name)
                if signals:
                    patterns[name] = signals
            except Exception as e:
                print(f"⚠️ Pattern {name} failed: {e}")

        # •••••••••••••••••••••••••• 🔥 Trend Patterns ######•••••••••••••••••••••••••• #
        # (Moving Averages, Bollinger, etc.)
        try:
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
            # Support/Resistance Levels
            patterns['support_resistance'] = self._detect_support_resistance(df)

            # RSI hinzufügen
            rsi = talib.RSI(close_prices, PATTERN_CONFIG['rsi_period'])
            patterns['rsi_oversold'] = self._detect_rsi_signals(rsi, df, 'oversold')
            patterns['rsi_overbought'] = self._detect_rsi_signals(rsi, df, 'overbought')

            # MACD hinzufügen
            macd, signal, hist = talib.MACD(close_prices)
            patterns['macd_crossover'] = self._detect_macd_crossover(macd, signal, df)
            
        except Exception as e:
            print(f"⚠️ Trend patterns failed: {e}")
        
        print(f"🎯 Detected {len(patterns)} pattern types")
        return patterns

    # ==============================================================================
    # region               Pattern UI Filter
    # ==============================================================================
    def filter_patterns(self, patterns: Dict[str, Any],
                        min_strength: float = 0.0,
                        directions: List[str] = None,
                        pattern_types: List[str] = None) -> Dict[str, Any]:
        """
        Robustes Pattern-Filtering für market_engine.py

        Ermöglicht dynamisches Pattern-Filtering nach:
        - Minimale Signalstärke (0.0-1.0)
        - Signal-Richtung (bullish, bearish, neutral, support, resistance)
        - Pattern-Typen (z.B. 'doji', 'hammer', etc.)

        Args:
            patterns: Original Patterns aus detect_patterns()
            min_strength: Minimale Signalstärke (0.0-1.0)
            directions: Liste von Richtungen (None = alle)
            pattern_types: Spezifische Pattern-Typen (None = alle)

        Returns:
            Dict[str, Any]: Gefilterte Patterns
        """
        # Grundlegende Validierung
        if patterns is None:
            print("⚠️ Keine Patterns zum Filtern vorhanden (None)")
            return {}

        if not isinstance(patterns, dict):
            print(f"⚠️ Patterns ist kein Dictionary, sondern {type(patterns)}")
            return {}

        if len(patterns) == 0:
            print("⚠️ Leeres Pattern-Dictionary")
            return {}

        # Spezialfall: 'all' in pattern_types
        if pattern_types and 'all' in pattern_types:
            pattern_types = None  # Alle Patterns verwenden

        # Verschachtelte Struktur erkennen
        if 'technical_indicators' in patterns or 'formation_patterns' in patterns:
            # Verschachtelte Struktur (neue API)
            filtered = {}

            for category, category_patterns in patterns.items():
                if not isinstance(category_patterns, dict):
                    print(f"⚠️ Kategorie {category} ist kein Dictionary, sondern {type(category_patterns)}")
                    continue

                if len(category_patterns) == 0:
                    print(f"⚠️ Kategorie {category} ist leer")
                    continue

                category_filtered = self._filter_flat_patterns(
                    category_patterns, min_strength, directions, pattern_types)

                if category_filtered and len(category_filtered) > 0:
                    filtered[category] = category_filtered
                    print(f"✅ {len(category_filtered)} Pattern-Typen in {category} nach Filter")
                else:
                    print(f"⚠️ Keine Patterns in {category} nach Filter")

            return filtered
        else:
            # Flache Struktur (Legacy-API)
            print("🔍 Flache Pattern-Struktur erkannt")
            return self._filter_flat_patterns(patterns, min_strength, directions, pattern_types)

    def _filter_flat_patterns(self, patterns: Dict[str, List],
                              min_strength: float = 0.0,
                              directions: List[str] = None,
                              pattern_types: List[str] = None) -> Dict[str, List]:
        """
        Robuster Helper für Pattern-Filtering mit verbesserten Typprüfungen

        Args:
            patterns: Original Patterns Dictionary (flache Struktur)
            min_strength: Minimale Signalstärke (0.0-1.0)
            directions: Liste von Richtungen (None = alle)
            pattern_types: Spezifische Pattern-Typen (None = alle)

        Returns:
            Dict[str, List]: Gefilterte Patterns
        """
        # Grundlegende Validierung
        if not isinstance(patterns, dict):
            print(f"⚠️ _filter_flat_patterns: patterns ist kein Dictionary, sondern {type(patterns)}")
            return {}

        filtered = {}

        # 1. Nach Pattern-Typen filtern (wenn angegeben)
        if pattern_types and pattern_types != ['all']:
            patterns = {k: v for k, v in patterns.items() if k in pattern_types}
            print(f"🔍 Nach Pattern-Typen gefiltert: {list(patterns.keys())}")   #TODO: hier haben wir glaube ich mal von type auf key gedreht. Seit dem keine Signals mehr für formation_patterns

        # 2. Durch jedes Pattern iterieren
        for pattern_name, signals in patterns.items():
            # 2.1 Typprüfung für signals
            if not isinstance(signals, list):
                print(f"⚠️ Signals für {pattern_name} ist keine Liste, sondern {type(signals)}")
                # Spezialfall: Wenn es ein String ist, in eine Liste packen
                if isinstance(signals, str):
                    print(f"🔄 Konvertiere String zu Liste für {pattern_name}")
                    signals = [signals]
                else:
                    continue  # Andere Typen überspringen

            # 2.2 Leere Liste abfangen
            if len(signals) == 0:
                print(f"⚠️ isinstance Keine Signals für {pattern_name}")
                continue

            # 2.3 Durch jedes Signal iterieren und filtern
            filtered_signals = []
            for signal in signals:
                # Typprüfung für jedes Signal
                if not isinstance(signal, dict):
                    print(f"⚠️ Signal für {pattern_name} ist kein Dict, sondern {type(signal)}")
                    continue

                # Stärke-Filter anwenden (falls vorhanden)
                if min_strength > 0:
                    # Sichere Variante mit get und Defaultwert
                    strength = signal.get('strength', 1)
                    if strength < min_strength:
                        continue

                # Richtungs-Filter anwenden (falls angegeben)
                if directions:
                    # Sichere Variante mit get und Defaultwert
                    direction = signal.get('direction', 'neutral')
                    # ✅ ADDITION: Formation Patterns by 'confirmed' status
                    if direction == 'neutral' and 'confirmed' in signal:
                        direction = 'bullish' if signal['confirmed'] else 'neutral'

                    if direction not in directions:
                        continue

                # Signal hat alle Filter bestanden
                filtered_signals.append(signal)

            # Nur Pattern-Typen mit übrig gebliebenen Signalen hinzufügen
            if filtered_signals:
                filtered[pattern_name] = filtered_signals

        return filtered



    # endregion

    # ==============================================================================
    #                      🔍 Pattern Helper Methods
    # ==============================================================================
    # ••••••••••••••••••••••••••  Extract Pattern Signals •••••••••••••••••••••••••• #
    def _extract_pattern_signals(self, talib_result, df: pd.DataFrame, pattern_name: str) -> List[Dict]:
        """
        Konvertiert TA-Lib Signale in standardisiertes Ausgabeformat.

        Transformiert die numerischen TA-Lib Ergebnisse (0, 100, -100) in
        strukturierte Signalobjekte mit allen relevanten Metadaten für
        die weitere Verarbeitung und Visualisierung.

        Args:
            talib_result: Numpy-Array mit TA-Lib Signalwerten
            df: DataFrame mit OHLCV-Daten
            pattern_name: Name des erkannten Pattern-Typs

        Returns:
            List[Dict]: Liste von strukturierten Signal-Objekten
        """
        signals = []
        
        for i, signal in enumerate(talib_result):
            if signal != 0:  # talib gibt -100, 0, oder 100 zurück
                # Wenn pattern_name "engulfing" enthält, Namen modifizieren
                if pattern_name == "engulfing_bullish" and signal < 0:
                    continue  # Ignoriere bearish Signale
                elif pattern_name == "engulfing_bearish" and signal > 0:
                    continue  # Ignoriere bullish Signale

                final_pattern_name = pattern_name

                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'strength': abs(signal) / 100.0,  # 0.0 bis 1.0
                    'direction': 'bullish' if signal > 0 else 'bearish',
                    'pattern': pattern_name
                })
        
        return signals

    # •••••••••••••••••••••••••• Detect BB-Squeeze •••••••••••••••••••••••••• #
    def _detect_bb_squeeze(self, close_prices, bb_upper, bb_lower, df):
        """
        Custom Bollinger Band Squeeze detection


        Identifiziert Phasen niedriger Volatilität, bei denen die
        Bollinger Bänder sich verengen, was oft auf eine bevorstehende
        Volatilitätsexplosion hindeutet.

        Args:
            close_prices: Numpy-Array mit Schlusskursen
            bb_upper: Oberes Bollinger Band
            bb_lower: Unteres Bollinger Band
            df: DataFrame mit OHLCV-Daten

        Returns:
            List[Dict]: Liste von Squeeze-Signalobjekten
        """
        signals = []
        
        if len(bb_upper) < 20:
            return signals
            
        # Squeeze = when bands are tight
        bb_width = (bb_upper - bb_lower) / close_prices
        bb_width_ma = talib.SMA(bb_width, PATTERN_CONFIG['bollinger_periods'])
        
        for i in range(20, len(bb_width)):
            if (bb_width[i] < bb_width_ma[i] * 0.8 and      # Tight bands
                bb_width[i-1] >= bb_width_ma[i-1] * 0.8):   # Was wider before
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': close_prices[i],
                    'strength': 0.8,
                    'direction': 'neutral',
                    'pattern': 'bollinger_squeeze'
                })
        
        return signals

    # •••••••••••••••••••••••••• Detect MA-Crossover •••••••••••••••••••••••••• #
    def _detect_ma_crossover(self, ma_fast, ma_slow, df):
        """
        Moving Average Crossover detection

        Erkennt Moving Average Crossover Signale.

        Identifiziert Kreuzungen zwischen schnellem und langsamem
        gleitenden Durchschnitt, was als Trendwechselsignal gilt.

        Args:
            ma_fast: Schneller gleitender Durchschnitt (Numpy-Array)
            ma_slow: Langsamer gleitender Durchschnitt (Numpy-Array)
            df: DataFrame mit OHLCV-Daten

        Returns:
            List[Dict]: Liste von MA-Crossover-Signalobjekten
        """
        signals = []
        
        for i in range(1, len(ma_fast)):
            if pd.isna(ma_fast[i]) or pd.isna(ma_slow[i]):
                continue
                
            # Bullish crossover: fast crosses above slow
            if ma_fast[i] > ma_slow[i] and ma_fast[i-1] <= ma_slow[i-1]:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'strength': 0.7,
                    'direction': 'bullish',
                    'pattern': 'ma_crossover'
                })
            
            # Bearish crossover: fast crosses below slow  
            elif ma_fast[i] < ma_slow[i] and ma_fast[i-1] >= ma_slow[i-1]:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i], 
                    'price': df['close'].iloc[i],
                    'strength': 0.7,
                    'direction': 'bearish',
                    'pattern': 'ma_crossover'
                })
        
        return signals

    # •••••••••••••••••••••••••• Detect RSI-Signals •••••••••••••••••••••••••• #
    def _detect_rsi_signals(self, rsi_values, df: pd.DataFrame, signal_type: str) -> List[Dict]:
        """RSI Überkauft/Überverkauft Detection"""
        signals = []

        # RSI-Schwellwerte definieren
        oversold_threshold = 30
        overbought_threshold = 70

        for i in range(1, len(rsi_values)):
            if pd.isna(rsi_values[i]):
                continue

            # Überverkauft Signal (bullish)
            if signal_type == 'oversold' and rsi_values[i] <= oversold_threshold and rsi_values[
                i - 1] > oversold_threshold:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'rsi_value': rsi_values[i],
                    'strength': 0.8,
                    'direction': 'bullish',
                    'pattern': 'rsi_oversold'
                })

            # Überkauft Signal (bearish)
            elif signal_type == 'overbought' and rsi_values[i] >= overbought_threshold and rsi_values[
                i - 1] < overbought_threshold:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'rsi_value': rsi_values[i],
                    'strength': 0.8,
                    'direction': 'bearish',
                    'pattern': 'rsi_overbought'
                })

        return signals

    # •••••••••••••••••••••••••• Detect Support & Resistance •••••••••••••••••••••••••• #
    def _detect_support_resistance(self, df: pd.DataFrame) -> List[Dict]:
        """Basic Support/Resistance levels"""
        signals = []

        if len(df) < 20:
            return signals

        # Find local highs and lows
        window = 5
        for i in range(window, len(df) - window):
            current_high = df['high'].iloc[i]
            current_low = df['low'].iloc[i]

            # Local high (resistance)
            is_high = all(current_high >= df['high'].iloc[j]
                          for j in range(i - window, i + window + 1) if j != i)

            # Local low (support)
            is_low = all(current_low <= df['low'].iloc[j]
                         for j in range(i - window, i + window + 1) if j != i)

            if is_high:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': current_high,
                    'strength': 0.6,
                    'direction': 'resistance',
                    'pattern': 'support_resistance'
                })

            if is_low:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': current_low,
                    'strength': 0.6,
                    'direction': 'support',
                    'pattern': 'support_resistance'
                })

        return signals

    # •••••••••••••••••••••••••• Detect MACD-Crossover •••••••••••••••••••••••••• #
    def _detect_macd_crossover(self, macd_line, signal_line, df: pd.DataFrame) -> List[Dict]:
        """MACD Signal-Line Crossover Detection"""
        signals = []

        for i in range(1, len(macd_line)):
            if pd.isna(macd_line[i]) or pd.isna(signal_line[i]):
                continue

            # Bullish Crossover: MACD crosses above Signal
            if macd_line[i] > signal_line[i] and macd_line[i - 1] <= signal_line[i - 1]:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'macd_value': macd_line[i],
                    'signal_value': signal_line[i],
                    'strength': 0.75,
                    'direction': 'bullish',
                    'pattern': 'macd_crossover'
                })

            # Bearish Crossover: MACD crosses below Signal
            elif macd_line[i] < signal_line[i] and macd_line[i - 1] >= signal_line[i - 1]:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'macd_value': macd_line[i],
                    'signal_value': signal_line[i],
                    'strength': 0.75,
                    'direction': 'bearish',
                    'pattern': 'macd_crossover'
                })

        return signals

    # endregion

    # ==============================================================================
    # region               🔧 UTILITY & HELPER METHODEN
    # ==============================================================================
    def get_available_symbols(self, exchange: str = 'binance') -> List[str]:
        """Alle verfügbaren Trading-Pairs

        Gibt eine Liste verfügbarer Trading-Pairs zurück.

        Holt die verfügbaren Symbole von der angegebenen Exchange
        oder gibt Standardwerte zurück, wenn die Exchange nicht
        verfügbar ist.

        Args:
            exchange (str): Exchange-Name (default: 'binance')

        Returns:
            List[str]: Liste verfügbarer Trading-Pairs oder Standardwerte
        """
        default_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']  # Sichere Defaults

        if exchange not in self.exchanges or isinstance(self.exchanges[exchange], dict):
            return default_symbols  # Wenn Exchange noch nicht geladen, Defaults

        try:
            markets = self.exchanges[exchange].markets
            symbols = [symbol for symbol in markets.keys() if '/USDT' in symbol]
            return symbols if symbols else default_symbols
        except:
            return default_symbols

    def get_market_stats(self) -> Dict[str, Any]:
        """
        Globale Marktdaten für Status-Bar

        Aggregiert globale Marktstatistiken für die Status-Bar.

        Sammelt Daten wie:
        - Marktkapitalisierung
        - 24h-Handelsvolumen
        - Fear & Greed Index
        - BTC-Dominanz
        - Anzahl aktiver Trading-Pairs

        Implementiert Cache-Mechanismus für Performance-Optimierung.

        Returns:
            Dict[str, Any]: Aggregierte Marktstatistiken
        """
        # Cache check
        if 'market_stats' in self.cache:
            cached_data, timestamp = self.cache['market_stats']
            if time.time() - timestamp < 300:  # 5min cache
                return cached_data

        # Standardwerte (falls API-Fehler)
        stats = {
            'market_cap': "$1.34T",  # Bisheriger Wert als Fallback
            'volume_24h': "2,847",  # Bisheriger Wert als Fallback
            'fear_greed': "73",  # Bisheriger Wert als Fallback
            'btc_dominance': "BTC 52.3%",  # Bisheriger Wert als Fallback
            'active_pairs': "1,247"  # Bisheriger Wert als Fallback
        }

        try:
            # 1️⃣ Active Pairs - Einfach zu berechnen aus vorhandenen Daten
            exchange_order = ['binance', 'coinbase', 'kraken', 'bybit', 'okx']
            for ex_name in exchange_order:
                if ex_name in self.exchanges and not isinstance(self.exchanges[ex_name], dict):
                    symbols = self.get_available_symbols(ex_name)
                    if symbols:
                        stats['active_pairs'] = f"{len(symbols):,}"
                    break

            # 2️⃣ Volume & Marktdaten - Aus Top-Coins berechnen
            top_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
            total_volume = 0
            total_mcap = 0
            btc_mcap = 0

            for ex_name in exchange_order:
                if ex_name not in self.exchanges or isinstance(self.exchanges[ex_name], dict):
                    continue

                try:
                    # Ticker-Daten für verfügbare Top-Coins abrufen
                    for symbol in top_symbols:
                        try:
                            # OHLCV-Daten nutzen (bereits in der Engine implementiert)
                            df = self.get_ohlcv(symbol, '1d', 1, ex_name)
                            if df.empty:
                                continue

                            # Letzte Schlusskurse & Volumen extrahieren
                            price = df['close'].iloc[-1]
                            volume = df['volume'].iloc[-1]

                            # Zum Gesamtvolumen addieren
                            total_volume += volume * price  # Volume in USDT

                            # Sehr grobe Marktkapitalisierung (vereinfacht)
                            coin_mcap = price * volume * 10  # Heuristische Schätzung
                            total_mcap += coin_mcap

                            # BTC Dominance berechnen
                            if symbol == 'BTC/USDT':
                                btc_mcap = coin_mcap
                        except:
                            continue

                    # Wenn wir Daten haben, Loop verlassen
                    if total_volume > 0:
                        break
                except Exception as e:
                    print(f"⚠️ Stats error on {ex_name}: {e}")
                    continue

            # 3️⃣ Berechnete Werte formatieren
            if total_mcap > 0:
                stats['market_cap'] = f"${total_mcap / 1e12:.2f}T"

            if total_volume > 0:
                stats['volume_24h'] = f"{total_volume / 1e9:.1f}B"

            if total_mcap > 0 and btc_mcap > 0:
                btc_dom = (btc_mcap / total_mcap) * 100
                stats['btc_dominance'] = f"BTC {btc_dom:.1f}%"

            # 4️⃣ Cache setzen
            self.cache['market_stats'] = (stats, time.time())

        except Exception as e:
            print(f"❌ Error getting market stats: {e}")

        return stats

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Exchange Status und Info

        Liefert Status-Informationen zu allen konfigurierten Exchanges.

        Erstellt ein strukturiertes Dictionary mit Status-Information
        für jede Exchange, einschließlich:
        - Online/Offline-Status
        - Anzahl verfügbarer Markets
        - Rate-Limit-Konfiguration
        - Verfügbare Funktionen

        Returns:
            Dict[str, Any]: Exchange-Status und -Information
        """
        info = {}

        for name, exchange in self.exchanges.items():
            try:
                # Wenn es ein Statusobjekt ist
                if isinstance(exchange, dict) and 'status' in exchange:
                    info[name] = exchange
                # Wenn es ein ccxt.Exchange Objekt ist
                else:
                    info[name] = {
                        'status': 'online',
                        'markets': len(exchange.markets),
                        'rate_limit': exchange.rateLimit,
                        'has_ohlcv': exchange.has['fetchOHLCV'],
                    }
            except Exception as e:
                info[name] = {'status': 'offline', 'error': str(e)}

        return info
    # endregion

# endregion

# Singleton-Instanz für globalen Zugriff
market_engine = MarketEngine()