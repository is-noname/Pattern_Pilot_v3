# core/market_engine.py     MARKET ENGINE CORE - Hauptkomponente v3.0
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

#==============================================================================
# region                🔄 MARKET ENGINE HAUPTKLASSE
#==============================================================================

class MarketEngine:
    """
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
        configs = [
            ('binance', ccxt.binance, {'rateLimit': 1200}),
            ('coinbase', ccxt.coinbase, {'rateLimit': 1000}),
            ('kraken', ccxt.kraken, {'rateLimit': 3000}),
            ('bybit', ccxt.bybit, {'rateLimit': 1000}),
            ('okx', ccxt.okx, {'rateLimit': 1000}),
        ]

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
        """In separatem Thread ausgeführt"""
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
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        # Cache check
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < 300:  # 5min cache
                print(f"💾 Cache hit: {symbol}")
                return cached_data
        
        # Exchange priority order
        if exchange and exchange in self.exchanges:
            # Prüfen ob Exchange online ist
            if isinstance(self.exchanges[exchange], dict):
                if self.exchanges[exchange].get('status') != 'online':
                    exchange = None  # Fallback, wenn Exchange nicht online
            exchange_order = [exchange] if exchange else []
        else:
            # Nur Online-Exchanges verwenden
            exchange_order = []

            # Fallback-Liste mit verfügbaren Exchanges
        if not exchange_order:
            for ex_name in ['binance', 'coinbase', 'kraken', 'bybit', 'okx']:
                # Nur Online-Exchanges zur Liste hinzufügen
                if ex_name in self.exchanges and not isinstance(self.exchanges[ex_name], dict):
                    exchange_order.append(ex_name)
                continue
                
            try:
                exchange_obj = self.exchanges[ex_name]
                print(f"🔄 Trying {ex_name} for {symbol}...")
                
                # Fetch OHLCV
                ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                if not ohlcv:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])
                
                # Convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('datetime').reset_index(drop=True)
                
                # Cache result
                self.cache[cache_key] = (df, time.time())
                
                print(f"✅ {ex_name}: {len(df)} candles")
                return df
                
            except Exception as e:
                print(f"❌ {ex_name} error: {e}")
                return pd.DataFrame()
        
        print(f"❌ No data found for {symbol}")
        return pd.DataFrame()
    # endregion

    # ==============================================================================
    # region               🎯 PATTERN DETECTION ENGINE
    # ==============================================================================
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
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

        # •••••••••••••••••••••••••• 🔥 Candlestick Patterns •••••••••••••••••••••••••• #
        candlestick_patterns = {
            'doji': talib.CDLDOJI,
            'hammer': talib.CDLHAMMER,
            'hanging_man': talib.CDLHANGINGMAN,
            'shooting_star': talib.CDLSHOOTINGSTAR,
            'engulfing_bullish': talib.CDLENGULFING,
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

        # •••••••••••••••••••••••••• 🔥 Trend Patterns •••••••••••••••••••••••••• #
        # (Moving Averages, Bollinger, etc.)
        try:
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices)
            patterns['bollinger_squeeze'] = self._detect_bb_squeeze(
                close_prices, bb_upper, bb_lower, df
            )
            
            # Moving Average Crossovers
            ma_fast = talib.SMA(close_prices, timeperiod=20)
            ma_slow = talib.SMA(close_prices, timeperiod=50)
            patterns['ma_crossover'] = self._detect_ma_crossover(
                ma_fast, ma_slow, df
            )
            # Support/Resistance Levels
            patterns['support_resistance'] = self._detect_support_resistance(df)
            
        except Exception as e:
            print(f"⚠️ Trend patterns failed: {e}")
        
        print(f"🎯 Detected {len(patterns)} pattern types")
        return patterns

    # ==============================================================================
    # region               Pattern UI Filter
    # ==============================================================================
    def filter_patterns(self, patterns: Dict[str, List],
                        min_strength: float = 0.0,
                        directions: List[str] = None,
                        pattern_types: List[str] = None) -> Dict[str, List]:
        """
        Dynamischer Pattern-Filter - nimmt ALLE Patterns, auch zukünftige

        Args:
            patterns: Original Patterns aus detect_patterns()
            min_strength: Minimale Signalstärke (0.0-1.0)
            directions: Liste von Richtungen ('bullish', 'bearish', 'neutral', 'support', 'resistance')
            pattern_types: Spezifische Pattern-Typen (wenn None, dann alle)

        Returns:
            Gefilterte Patterns
        """
        if not patterns:
            return {}

        filtered = {}

        # 1. Erst nach Pattern-Typen filtern (wenn angegeben)
        if pattern_types:
            patterns = {k: v for k, v in patterns.items() if k in pattern_types}

        # 2. Für jedes Pattern die Signale nach Strength/Direction filtern
        for pattern_name, signals in patterns.items():
            # Leere Signal-Liste für diesen Pattern-Typ
            filtered_signals = []

            for signal in signals:
                # Strength-Filter anwenden
                if signal.get('strength', 0) < min_strength:
                    continue

                # Direction-Filter anwenden (wenn angegeben)
                if directions and signal.get('direction') not in directions:
                    continue

                # Signal hat alle Filter bestanden
                filtered_signals.append(signal)

            # Nur Pattern-Typen mit Signalen behalten
            if filtered_signals:
                filtered[pattern_name] = filtered_signals

        return filtered

    # endregion

    # ==============================================================================
    #                      🔍 Pattern Helper Methods
    # ==============================================================================
    def _extract_pattern_signals(self, talib_result, df: pd.DataFrame, 
                                pattern_name: str) -> List[Dict]:
        """Konvertiert talib signals zu readable format"""
        signals = []
        
        for i, signal in enumerate(talib_result):
            if signal != 0:  # talib gibt -100, 0, oder 100 zurück
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'strength': abs(signal) / 100.0,  # 0.0 bis 1.0
                    'direction': 'bullish' if signal > 0 else 'bearish',
                    'pattern': pattern_name
                })
        
        return signals
    
    def _detect_bb_squeeze(self, close_prices, bb_upper, bb_lower, df):
        """Custom Bollinger Band Squeeze detection"""
        signals = []
        
        if len(bb_upper) < 20:
            return signals
            
        # Squeeze = when bands are tight
        bb_width = (bb_upper - bb_lower) / close_prices
        bb_width_ma = talib.SMA(bb_width, timeperiod=20)
        
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

    def _detect_ma_crossover(self, ma_fast, ma_slow, df):
        """Moving Average Crossover detection"""
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

    # endregion

    # ==============================================================================
    # region               🔧 UTILITY & HELPER METHODEN
    # ==============================================================================
    def get_available_symbols(self, exchange: str = 'binance') -> List[str]:
        """Alle verfügbaren Trading-Pairs"""
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
        """Globale Marktdaten für Status-Bar"""
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
            top_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
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
        """Exchange Status und Info"""
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

# Singleton instance
market_engine = MarketEngine()