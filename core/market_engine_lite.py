# core/market_engine_lite.py - Falls TA-Lib Installation nervt
"""
Market Engine Lite - TA-Lib-freie Version !! deaktiviert !!

Leichtgewichtige Alternative zur vollständigen market_engine,
die ohne externe TA-Lib-Abhängigkeit funktioniert. Implementiert
grundlegende Pattern-Erkennung mit reinem Python/NumPy.

Ideal für schnelle Tests oder Systeme ohne TA-Lib-Installation.
"""
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import time

class MarketEngine:
    """
    🚀 TA-Lib-freie Version für schnellen Start
    
    Nutzt nur ccxt + numpy für Basic Pattern Detection
    Kann später easy auf full talib erweitert werden
    """
    
    def __init__(self):
        self.exchanges = self._init_exchanges()
        self.cache = {}
        print(f"✅ MarketEngine Lite: {len(self.exchanges)} Exchanges bereit")

    # ==============================================================================
    #                      _init_exchanges
    # ==============================================================================
    def _init_exchanges(self) -> Dict[str, ccxt.Exchange]:
        """Same wie full version"""
        exchanges = {}
        configs = [
            ('binance', ccxt.binance, {'rateLimit': 1200}),
            ('coinbase', ccxt.coinbase, {'rateLimit': 1000}),
            ('kraken', ccxt.kraken, {'rateLimit': 3000}),
        ]
        
        for name, exchange_class, config in configs:
            try:
                exchanges[name] = exchange_class(config)
                exchanges[name].load_markets()
                print(f"📡 {name}: {len(exchanges[name].markets)} markets")
            except Exception as e:
                print(f"❌ {name} failed: {e}")
        
        return exchanges

    # ==============================================================================
    #                      get_ohlcv
    # ==============================================================================
    def get_ohlcv(self, symbol: str, timeframe: str = '1d', 
                  limit: int = 500, exchange: str = None) -> pd.DataFrame:
        """Same wie full version - ccxt braucht kein TA-Lib"""
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < 300:
                return cached_data
        
        exchange_order = ['binance', 'coinbase', 'kraken'] if not exchange else [exchange]
        
        for ex_name in exchange_order:
            if ex_name not in self.exchanges:
                continue
                
            try:
                exchange_obj = self.exchanges[ex_name]
                ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                if not ohlcv:
                    continue
                
                df = pd.DataFrame(ohlcv, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('datetime').reset_index(drop=True)
                
                self.cache[cache_key] = (df, time.time())
                print(f"✅ {ex_name}: {len(df)} candles")
                return df
                
            except Exception as e:
                print(f"❌ {ex_name} error: {e}")
                continue
        
        return pd.DataFrame()

    # ==============================================================================
    #                      detect_patterns
    # ==============================================================================
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        🎯 Lite Pattern Detection ohne TA-Lib
        
        Basic Patterns mit numpy - funktioniert sofort!
        """
        if df.empty or len(df) < 10:
            return {}
        
        patterns = {}
        
        # 🕯️ Simple Candlestick Patterns (ohne TA-Lib)
        patterns['doji'] = self._detect_doji(df)
        patterns['hammer'] = self._detect_hammer(df)
        patterns['engulfing'] = self._detect_engulfing(df)
        patterns['ma_crossover'] = self._detect_ma_crossover(df)
        patterns['support_resistance'] = self._detect_support_resistance(df)
        
        print(f"🎯 Detected {len(patterns)} pattern types (Lite)")
        return patterns

    # ==============================================================================
    #                      filter_patterns
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
        print(f"DEBUG: patterns type: {type(patterns)}")
        if isinstance(patterns, str):
            print(f"DEBUG: patterns is string: {patterns}")

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
        print(f"DEBUG: filtered: {type(filtered)}")
        if isinstance(filtered, str):
            print(f"DEBUG: filtered is string: {filtered}")
    # ==============================================================================
    #                      _detect_doji
    #==============================================================================
    def _detect_doji(self, df: pd.DataFrame) -> List[Dict]:
        """Simple Doji detection"""
        signals = []
        
        for i in range(len(df)):
            open_price = df['open'].iloc[i]
            close_price = df['close'].iloc[i]
            high_price = df['high'].iloc[i]
            low_price = df['low'].iloc[i]
            
            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            
            # Doji: Body < 10% of total range
            if total_range > 0 and body_size / total_range < 0.1:
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': close_price,
                    'strength': 0.7,
                    'direction': 'neutral',
                    'pattern': 'doji'
                })
        
        return signals

    # ==============================================================================
    #                      _detect_hammer
    # ==============================================================================
    def _detect_hammer(self, df: pd.DataFrame) -> List[Dict]:
        """Simple Hammer detection"""
        signals = []
        
        for i in range(len(df)):
            open_price = df['open'].iloc[i]
            close_price = df['close'].iloc[i]
            high_price = df['high'].iloc[i]
            low_price = df['low'].iloc[i]
            
            body_size = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            
            # Hammer: Long lower shadow, short upper shadow
            if (lower_shadow > body_size * 2 and 
                upper_shadow < body_size * 0.5 and
                body_size > 0):
                
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': close_price,
                    'strength': 0.8,
                    'direction': 'bullish',
                    'pattern': 'hammer'
                })
        
        return signals

    # ==============================================================================
    #                      _detect_engulfing
    # ==============================================================================
    def _detect_engulfing(self, df: pd.DataFrame) -> List[Dict]:
        """Simple Engulfing pattern"""
        signals = []
        
        for i in range(1, len(df)):
            # Previous candle
            prev_open = df['open'].iloc[i-1]
            prev_close = df['close'].iloc[i-1]
            
            # Current candle  
            curr_open = df['open'].iloc[i]
            curr_close = df['close'].iloc[i]
            
            # Bullish Engulfing
            if (prev_close < prev_open and  # Previous red
                curr_close > curr_open and  # Current green
                curr_open < prev_close and  # Opens below prev close
                curr_close > prev_open):    # Closes above prev open
                
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': curr_close,
                    'strength': 0.9,
                    'direction': 'bullish',
                    'pattern': 'engulfing'
                })
            
            # Bearish Engulfing
            elif (prev_close > prev_open and  # Previous green
                  curr_close < curr_open and  # Current red
                  curr_open > prev_close and  # Opens above prev close
                  curr_close < prev_open):    # Closes below prev open
                
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': curr_close,
                    'strength': 0.9,
                    'direction': 'bearish',
                    'pattern': 'engulfing'
                })
        
        return signals

    # ==============================================================================
    #                      _detect_ma_crossover
    # ==============================================================================
    def _detect_ma_crossover(self, df: pd.DataFrame) -> List[Dict]:
        """Moving Average Crossover ohne TA-Lib"""
        signals = []
        
        if len(df) < 50:
            return signals
        
        # Simple Moving Averages
        df['ma_fast'] = df['close'].rolling(window=20).mean()
        df['ma_slow'] = df['close'].rolling(window=50).mean()
        
        for i in range(1, len(df)):
            if pd.isna(df['ma_fast'].iloc[i]) or pd.isna(df['ma_slow'].iloc[i]):
                continue
            
            # Bullish crossover
            if (df['ma_fast'].iloc[i] > df['ma_slow'].iloc[i] and 
                df['ma_fast'].iloc[i-1] <= df['ma_slow'].iloc[i-1]):
                
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'strength': 0.7,
                    'direction': 'bullish',
                    'pattern': 'ma_crossover'
                })
            
            # Bearish crossover
            elif (df['ma_fast'].iloc[i] < df['ma_slow'].iloc[i] and 
                  df['ma_fast'].iloc[i-1] >= df['ma_slow'].iloc[i-1]):
                
                signals.append({
                    'index': i,
                    'datetime': df['datetime'].iloc[i],
                    'price': df['close'].iloc[i],
                    'strength': 0.7,
                    'direction': 'bearish',
                    'pattern': 'ma_crossover'
                })
        
        return signals

    # ==============================================================================
    #                      _detect_support_resistance
    # ==============================================================================
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
                         for j in range(i-window, i+window+1) if j != i)
            
            # Local low (support)  
            is_low = all(current_low <= df['low'].iloc[j]
                        for j in range(i-window, i+window+1) if j != i)
            
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

    # ==============================================================================
    #                      get_available_symbols
    # ==============================================================================
    def get_available_symbols(self, exchange: str = 'binance') -> List[str]:
        """Same wie full version"""
        if exchange not in self.exchanges:
            return []
        
        try:
            markets = self.exchanges[exchange].markets
            return [symbol for symbol in markets.keys() if '/USDT' in symbol][:100]
        except:
            return []

    # ==============================================================================
    #                      get_exchange_info
    # ==============================================================================
    def get_exchange_info(self) -> Dict[str, Any]:
        """Same wie full version"""
        info = {}
        for name, exchange in self.exchanges.items():
            try:
                info[name] = {
                    'status': 'online',
                    'markets': len(exchange.markets),
                    'rate_limit': exchange.rateLimit,
                }
            except Exception as e:
                info[name] = {'status': 'error', 'error': str(e)}
        return info


# Singleton
market_engine = MarketEngine()