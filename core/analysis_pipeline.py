# core/analysis_pipeline.py
"""
AnalysisPipeline - Zentrale Orchestrierung für Pattern-Detection und -Analyse

Production Singleton Pipeline optimiert für:
- Single-Asset Multi-Timeframe Analysis
- Traditional Trading Pairs (BTC/USDT)
- Contract Addresses (0x...) - Future DexScreener Integration
- Backward-Compatibility mit app.py Interfaces

Koordiniert market_engine, pattern_manager und analyze_manager
"""
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from datetime import datetime
import time


class AnalysisPipeline:
    """
    Production Singleton Pipeline für Single-Asset Multi-Timeframe Analysis

    Design Principles:
    - Fail-safe operation (graceful degradation)
    - Interface preservation (app.py compatibility)
    - Resource-optimized für Token Diversity
    - Live Terminal Feedback für Debugging
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnalysisPipeline, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Core Dependencies (Safe Import)
        try:
            from core.market_engine import market_engine
            self.market_engine = market_engine
            print("✅ market_engine loaded successfully")
        except Exception as e:
            print(f"❌ CRITICAL: market_engine initialization failed: {e}")
            self.market_engine = None

        # Lazy-loaded Components (Avoid Circular Imports)
        self._pattern_manager = None
        self._analyze_manager = None
        self._cache_instance = None

        # Resource Management für Token Diversity
        self._symbol_cache = {}  # Current analysis cache per symbol
        self._timeframe_cache = {}  # Multi-timeframe data storage
        self._analysis_results = {}  # Bounded result cache
        self._contract_metadata_cache = {}  # Contract address metadata

        # Resource Limits für Memory Management
        self.max_cached_symbols = 5  # LRU für verschiedene Tokens
        self.max_timeframe_data = 4  # Limit für Multi-Timeframe Storage
        self.max_analysis_results = 10  # Bounded analysis history

        # Pipeline State
        self.pipeline_active = True
        self.last_error = None

        # Component Health Validation
        self._validate_components()
        print("✅ AnalysisPipeline Singleton initialized")

    # ============================================================================
    # region               🔧 COMPONENT LAZY LOADING
    # ============================================================================

    @property
    def pattern_manager(self):
        """Lazy loading pattern_manager mit Error Handling"""
        if self._pattern_manager is None:
            try:
                from core.patterns.chart_patterns.pattern_manager import pattern_manager
                self._pattern_manager = pattern_manager
                print("✅ pattern_manager loaded successfully")
            except ImportError as e:
                print(f"⚠️  pattern_manager unavailable: {e}")
                self._pattern_manager = False  # Marker für failed load
        return self._pattern_manager if self._pattern_manager is not False else None

    @property
    def analyze_manager(self):
        """Lazy loading analyze_manager mit Fallback"""
        if self._analyze_manager is None:
            try:
                from analyze.analyze_manager import analyze_manager
                self._analyze_manager = analyze_manager
                print("✅ analyze_manager loaded successfully")
            except ImportError as e:
                print(f"⚠️  analyze_manager unavailable: {e}")
                self._analyze_manager = False
        return self._analyze_manager if self._analyze_manager is not False else None

    @property
    def cache_instance(self):
        """Lazy loading cache_instance"""
        if self._cache_instance is None:
            try:
                from cache.cache_manager import cache_instance
                self._cache_instance = cache_instance
                print("✅ cache_instance loaded successfully")
            except ImportError as e:
                print(f"⚠️  cache_instance unavailable: {e}")
                self._cache_instance = False
        return self._cache_instance if self._cache_instance is not False else None

    # endregion

    # ============================================================================
    # region               📊 CORE ANALYSIS METHODS
    # ============================================================================

    def analyze_symbol(self, symbol: str, timeframe: str = "1d", limit: int = 200,
                       exchange: str = None) -> Dict[str, Any]:
        """
        Single Symbol Analysis - Core Pipeline Method

        Backward-compatible mit app.py - behält market_engine Interface

        Args:
            symbol: Trading pair oder Contract Address
            timeframe: Zeitrahmen (1d, 3d, 1w, 1M)
            limit: Anzahl Candles
            exchange: Optional Exchange override

        Returns:
            Dict mit analysis results
        """
        print(f"🔍 Pipeline analyzing {symbol} on {timeframe}")

        # Symbol Normalization für Future Contract Address Support
        symbol_info = self._normalize_symbol_identifier(symbol)

        try:
            # 1. OHLCV Data Acquisition
            df = self.market_engine.get_ohlcv(symbol, timeframe, limit, exchange)
            if df.empty:
                print(f"❌ No data available for {symbol}")
                return {'error': 'No data available'}

            # 2. Technical Patterns (market_engine)
            technical_patterns = self.market_engine.detect_patterns(df)

            # 3. Chart Formation Patterns (pattern_manager) - Optional
            formation_patterns = {}
            if self.pattern_manager:
                try:
                    formation_patterns = self.pattern_manager.detect_patterns(df, timeframe)
                    print(f"✅ Formation patterns detected: {len(formation_patterns)}")
                except Exception as e:
                    print(f"⚠️  Formation pattern detection failed: {e}")

            # 4. Analysis Aggregation (analyze_manager) - Optional
            analysis_summary = None
            if self.analyze_manager:
                try:
                    # TODO: Implementation pending analyze_manager integration
                    pass
                except Exception as e:
                    print(f"⚠️  Analysis aggregation failed: {e}")

            # 5. Result Compilation
            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'symbol_info': symbol_info,
                'data': df,
                'patterns': {
                    'technical_indicators': technical_patterns,
                    'formation_patterns': formation_patterns
                },
                'analysis_summary': analysis_summary,
                'timestamp': datetime.now()
            }

            # 6. Cache Management
            self._cache_analysis_result(symbol, timeframe, result)

            print(f"✅ Analysis complete for {symbol} ({timeframe})")
            return result

        except Exception as e:
            print(f"❌ Analysis failed for {symbol}: {e}")
            self.last_error = str(e)
            return {'error': str(e), 'symbol': symbol, 'timeframe': timeframe}

    def analyze_multi_timeframe(self, symbol: str, timeframes: List[str],
                                limit: int = 200) -> Dict[str, Dict[str, Any]]:
        """
        Multi-Timeframe Analysis für Single Asset

        Kritischer Use-Case für Trading Analysis

        Args:
            symbol: Trading pair oder Contract Address
            timeframes: Liste von Zeitrahmen ["1d", "3d", "1w", "1M"]
            limit: Anzahl Candles pro Timeframe

        Returns:
            Dict[timeframe, analysis_result]
        """
        print(f"🔍 Multi-Timeframe Analysis für {symbol}: {timeframes}")

        results = {}

        for timeframe in timeframes:
            print(f"📊 Processing {timeframe} timeframe...")

            # Sequential Processing (Memory-optimiert)
            analysis = self.analyze_symbol(symbol, timeframe, limit)
            results[timeframe] = analysis

            # Memory Management zwischen Timeframes
            self._cleanup_intermediate_data()

        print(f"✅ Multi-Timeframe Analysis complete: {len(results)} timeframes")
        return results

    # endregion

    # ============================================================================
    # region               🔧 UTILITY & HELPER METHODS
    # ============================================================================

    def _normalize_symbol_identifier(self, symbol: str) -> Dict[str, str]:
        """
        Future-Proof Symbol Normalization für Asset Type Detection

        Supports:
        - Traditional Pairs: "BTC/USDT"
        - Contract Addresses: "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"
        - DexScreener Integration: Custom formats (Future)
        """
        if symbol.startswith("0x") and len(symbol) == 42:
            # Ethereum Contract Address
            return {
                "type": "contract_address",
                "identifier": symbol,
                "source": "dexscreener",
                "network": "ethereum"
            }
        elif "/" in symbol:
            # Traditional Trading Pair
            return {
                "type": "trading_pair",
                "identifier": symbol,
                "source": "exchange",
                "network": "centralized"
            }
        else:
            # Future: Additional identifier types
            return {
                "type": "unknown",
                "identifier": symbol,
                "source": "auto_detect",
                "network": "unknown"
            }

    def _validate_components(self):
        """Component Health Validation mit Terminal Feedback"""
        if not self.market_engine:
            print("🚨 Pipeline operating in degraded mode - market_engine unavailable")
            return False

        if not hasattr(self.market_engine, 'get_ohlcv'):
            print("⚠️  market_engine missing get_ohlcv method")
            return False

        if not hasattr(self.market_engine, 'detect_patterns'):
            print("⚠️  market_engine missing detect_patterns method")
            return False

        print("🔋 Core components validated")
        return True

    # endregion

    # ============================================================================
    # region               💾 CACHE & RESOURCE MANAGEMENT
    # ============================================================================

    def _cache_analysis_result(self, symbol: str, timeframe: str, result: Dict[str, Any]):
        """Cache Management für Analysis Results"""
        cache_key = f"{symbol}_{timeframe}"

        # Bounded Cache: Limit analysis results
        if len(self._analysis_results) >= self.max_analysis_results:
            oldest_key = next(iter(self._analysis_results))
            del self._analysis_results[oldest_key]
            print(f"🧹 Evicted oldest analysis: {oldest_key}")

        self._analysis_results[cache_key] = result
        print(f"💾 Cached analysis: {cache_key}")

    def _cleanup_intermediate_data(self):
        """Memory Management zwischen Multi-Timeframe Analysen"""
        # Clear temporary DataFrames from memory
        import gc

        # Force garbage collection
        collected = gc.collect()
        if collected > 0:
            print(f"🧹 Garbage collection freed {collected} objects")

    def _manage_cache_expansion(self, symbol: str):
        """
        LRU-basiertes Cache Management für Token Diversity

        Critical für Contract Address Integration
        """
        if len(self._symbol_cache) >= self.max_cached_symbols:
            # Remove oldest cached symbol
            oldest_symbol = next(iter(self._symbol_cache))
            removed_data = self._symbol_cache.pop(oldest_symbol)

            # Calculate memory footprint
            memory_kb = self._get_memory_footprint(removed_data)
            print(f"🧹 Evicted cache for {oldest_symbol}: {memory_kb:.1f} KB")

    def _get_memory_footprint(self, data: Any) -> float:
        """Estimate memory footprint of cached data"""
        try:
            if isinstance(data, pd.DataFrame):
                return data.memory_usage(deep=True).sum() / 1024
            elif isinstance(data, dict):
                return len(str(data)) / 1024  # Rough estimate
            else:
                return 0.0
        except:
            return 0.0

    def cleanup_resources(self):
        """Explicit resource cleanup für Long-Running Processes"""
        # Clear analysis results cache
        if len(self._analysis_results) > 5:
            keep_keys = list(self._analysis_results.keys())[-5:]
            self._analysis_results = {k: self._analysis_results[k] for k in keep_keys}
            print(f"🧹 Cleaned analysis cache, kept {len(keep_keys)} recent results")

        # Clear symbol cache
        self._symbol_cache.clear()
        self._timeframe_cache.clear()

        # Force garbage collection
        import gc
        collected = gc.collect()
        print(f"🧹 Resource cleanup complete: {collected} objects freed")

    def __del__(self):
        """Destructor für automatic cleanup"""
        try:
            self.cleanup_resources()
            print("🔄 AnalysisPipeline cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

    # endregion

    # ============================================================================
    # region               📈 BACKWARD COMPATIBILITY INTERFACE
    # ============================================================================

    def get_analysis_summary(self, symbol: str, timeframe: str = "1d") -> Optional[Dict[str, Any]]:
        """
        Get cached analysis summary - Backward compatible method

        Ermöglicht app.py Zugriff auf Pipeline-Results ohne vollständige Re-Analysis
        """
        cache_key = f"{symbol}_{timeframe}"

        if cache_key in self._analysis_results:
            result = self._analysis_results[cache_key]
            return {
                'patterns': result.get('patterns', {}),
                'symbol_info': result.get('symbol_info', {}),
                'timestamp': result.get('timestamp'),
                'cached': True
            }

        return None

    def get_pattern_count(self, symbol: str, timeframe: str = "1d") -> int:
        """
        Get total pattern count - Useful für app.py Pattern Count Badge
        """
        summary = self.get_analysis_summary(symbol, timeframe)
        if not summary:
            return 0

        patterns = summary.get('patterns', {})
        total_count = 0

        for pattern_category, pattern_dict in patterns.items():
            if isinstance(pattern_dict, dict):
                total_count += sum(len(pattern_list) for pattern_list in pattern_dict.values())
            elif isinstance(pattern_dict, list):
                total_count += len(pattern_dict)

        return total_count

    # endregion


# ============================================================================
# region               🏭 SINGLETON INSTANCE CREATION
# ============================================================================

# Global Singleton Instance für app.py Compatibility
analysis_pipeline = AnalysisPipeline()

# endregion