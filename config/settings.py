# config/settings.py - ZENTRALE KONFIGURATION - Settings für Pattern Pilot
"""
Zentrale Konfiguration für Pattern Pilot

Enthält alle wichtigen Einstellungen für:
- Exchange-Verbindungen und API-Parameter
- Chart-Darstellung und Farbschemata
- Pattern-Konfiguration und visuelles Styling
- Cache-Einstellungen und Entwicklungsoptionen

Dient als zentrale Steuerung für das gesamte System.
"""
import os
from typing import Dict, List


# ==============================================================================
# region               📡 EXCHANGE KONFIGURATION
# ==============================================================================
EXCHANGE_CONFIG = {
    'binance': {
        'rateLimit': 1200,
        'enableRateLimit': True,
        'sandbox': False,  # True für Testing
    },
    'coinbase': {
        'rateLimit': 1000,
        'enableRateLimit': True,
    },
    'kraken': {
        'rateLimit': 3000,
        'enableRateLimit': True,
    },
    'bybit': {
        'rateLimit': 1000,
        'enableRateLimit': True,
    },
    'okx': {
        'rateLimit': 1000,
        'enableRateLimit': True,
    }
}
# endregion

# ==============================================================================
# region               🎨 UI KONFIGURATION
# ==============================================================================
UI_CONFIG = {
    'page_title': 'Holy Panel v3',
    'page_icon': '🚀',
    'layout': 'wide',
    'sidebar_width': 300,
    'default_symbols': [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT'
    ],
    'default_timeframes': ['1m', '5m', '15m', '1h', '4h', '1d', '3d', '1w', '1M'],
    'default_directions': ["bullish", "bearish", "support", "resistance", "neutral"],
    'clock_interval': 2000, # 2 Sekunde in Millisekunden
    'exchange_interval': 1000, # Polling-Frequenz: 1000ms
}
# endregion

# ==============================================================================
# region               📊 CHART KONFIGURATION
# ==============================================================================
CHART_CONFIG = {
    'default_candles': 200,
    'max_candles': 1000,
    'default_timeframe': "1d",
    'theme': 'plotly_dark',
    'height': 800,
    'colors': {
        'bullish': '#06fc99',
        'bearish': '#f44336',
        'neutral': '#ffaa00',
        'background': '#0e1117'
    },
    'candle_colors': {
        'up': '#06fc99',
        'down': '#f44336'
    }
}
# endregion


################################################################################
#
#                         🧩 PATTERN KONFIGURATION
#
#
################################################################################
# ==============================================================================
# region
# ==============================================================================
PATTERN_CONFIG = {

    # •••••••••••••••••••••••••• Pattern Aktivierung •••••••••••••••••••••••••• #
    # (aktuell nur Candlestick-Pattern)
    'candlestick_patterns': [
        'doji',
        'hammer',
        'hanging_man',
        'shooting_star',
        'engulfing_bullish',
        'engulfing_bearish',
        'morning_star',
        'evening_star',
        'three_white_soldiers',
        'three_black_crows',
        'harami',
        'piercing',
        'dark_cloud',
        'inverted_hammer',  # Umgedrehter Hammer
        'marubozu',  # Volle Kerze ohne Schatten
        'spinning_top',  # Spinning Top (Unentschlossenheit)
        'dragonfly_doji',  # Dragonfly Doji
        'kicking',  # Kicking Pattern (starker Trend)
        'tasuki_gap',  # Tasuki Gap (Trendfortsetzung)
        'breakaway',  # Breakaway (Trendstart)
        'doji_star',  # Doji Star (potentielle Umkehr)

        # Multi-Candle Patterns (auch implementiert)
        'bollinger_squeeze',  # BB Squeeze
        'ma_crossover',  # MA Crossover
        'support_resistance',  # S/R Levels
        'rsi_oversold',
        'rsi_overbought',
        'macd_crossover'
    ],

    # ==============================================================================
    #                      🔧 Custom Pattern Settings 🔧
    # ==============================================================================
    # •••••••••••••••••••••••••• 🔧hier TIMEFRAME_CONFIGS implementieren 🔧  •••••••••••••••••••••••••• #
    'bollinger_periods': 20,        # Standard-Lookback-Periode für BB-Berechnung
    'rsi_period': 14,               # Lookback-Periode für RSI-Berechnung 14-Perioden RSI ist der Industrie-Standard seit 1978. Overbought >70, Oversold <30
    'support_resistance_window': 5, # Lokale Extrema-Fenster
    # MA_Cross def
    'ma_crossover_fast': 20,        # Schneller MA für Crossover-Signale
    'ma_crossover_slow': 50,        # Langsamer MA für Trend-Identifikation
    
    # Minimum pattern strength to display     <--Filter Panel Default??? nach CHART KONFIGURATION verschieben ???
    'min_pattern_strength': 0.5,

    # •••••••••••••••••••••••••• 🎨 Chart Pattern Visualisierung •••••••••••••••••••••••••• #
    'pattern_styles': {
        # Canlde-Patterns
        'doji': {'symbol': 'circle', 'color': '#117e23', 'size': 3, 'emoji': '🎯'},
        'hammer': {'symbol': 'triangle-up', 'color': '#00ff88', 'size': 4, 'emoji': '🔨'},
        'engulfing_bullish': {'symbol': 'star', 'color': '#ff0080', 'size': 5, 'emoji': '🌟'},
        'engulfing_bearish': {'symbol': 'star', 'color': '#ff4444', 'size': 5, 'emoji': '🌟'},
        'hanging_man': {'symbol': 'triangle-down', 'color': '#ff4444', 'size': 4, 'emoji': '⚠️'},
        'shooting_star': {'symbol': 'star-triangle-up', 'color': '#ff6600', 'size': 4, 'emoji': '⭐'},
        'morning_star': {'symbol': 'star-square', 'color': '#66ff66', 'size': 4, 'emoji': '🌅'},
        'evening_star': {'symbol': 'star-diamond', 'color': '#ff3366', 'size': 4, 'emoji': '🌆'},
        'three_white_soldiers': {'symbol': 'arrow-up', 'color': '#44ff44', 'size': 5, 'emoji': '⬆️'},
        'three_black_crows': {'symbol': 'arrow-down', 'color': '#ff4444', 'size': 5, 'emoji': '⬇️'},
        'harami': {'symbol': 'hourglass', 'color': '#ffaa44', 'size': 3, 'emoji': '⏳'},
        'piercing': {'symbol': 'triangle-up-open', 'color': '#44aa44', 'size': 4, 'emoji': '🔺'},
        'dark_cloud': {'symbol': 'triangle-down-open', 'color': '#aa4444', 'size': 4, 'emoji': '🔻'},
        'inverted_hammer': {'symbol': 'triangle-up-open', 'color': '#ff9900', 'size': 4, 'emoji': '🔨'},
        'marubozu': {'symbol': 'diamond', 'color': '#00ffcc', 'size': 4, 'emoji': '📊'},
        'spinning_top': {'symbol': 'circle-open', 'color': '#aaaaaa', 'size': 3, 'emoji': '🔄'},
        'dragonfly_doji': {'symbol': 'triangle-down-dot', 'color': '#33ccff', 'size': 4, 'emoji': '🐉'},
        'kicking': {'symbol': 'x', 'color': '#ff3366', 'size': 5, 'emoji': '👟'},
        'tasuki_gap': {'symbol': 'diamond-tall', 'color': '#66ff66', 'size': 4, 'emoji': '🧩'},
        'breakaway': {'symbol': 'star-diamond', 'color': '#ff6600', 'size': 5, 'emoji': '💥'},
        'doji_star': {'symbol': 'star', 'color': '#ffff00', 'size': 4, 'emoji': '⭐'},
        # Multi-Candle Patterns-Styles
        'support_resistance': {'symbol': 'square', 'color': '#aa00ff', 'size': 3, 'emoji': '🔷'},
        'ma_crossover': {'symbol': 'x', 'color': '#ff00dd', 'size': 6, 'emoji': '💎'},
        'macd_crossover': {'symbol': 'x-open', 'color': '#ff00dd', 'size': 5, 'emoji': '⚡'},
        'rsi_oversold': {'symbol': 'triangle-up', 'color': '#00ff00', 'size': 4, 'emoji': '📈'},
        'rsi_overbought': {'symbol': 'triangle-down', 'color': '#ff0000', 'size': 4, 'emoji': '📉'},
        'bollinger_squeeze': {'symbol': 'diamond-wide', 'color': '#117e23', 'size': 5, 'emoji': '💥'},
        #Chart-Patterns
    }
}
# endregion

# ==============================================================================
# region              💾 CACHE KONFIGURATION
# ==============================================================================
CACHE_CONFIG = {
    'enabled': True,
    'ttl_seconds': 300,  # 5 Minuten
    'type': 'memory',    # 'memory' oder 'redis'
    'redis_url': 'redis://localhost:6379/0'
}
# endregion

# ==============================================================================
# region               🔧 DEVELOPMENT SETTINGS
# ==============================================================================
DEV_CONFIG = {
    'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'enable_profiling': False,
    'mock_data': False  # True für Development ohne API calls
}

# API Keys (falls Premium-Features benötigt)
API_KEYS = {
    # Meiste ccxt Exchanges brauchen keine Keys für Public Data
    'binance': {
        'apiKey': os.getenv('BINANCE_API_KEY', ''),
        'secret': os.getenv('BINANCE_SECRET', ''),
    },
    'coinbase': {
        'apiKey': os.getenv('COINBASE_API_KEY', ''),
        'secret': os.getenv('COINBASE_SECRET', ''),
        'passphrase': os.getenv('COINBASE_PASSPHRASE', ''),
    }
}

# 📱 Mobile Optimierung
MOBILE_CONFIG = {
    'responsive_charts': True,
    'touch_friendly': True,
    'simplified_ui': True,  # Weniger Buttons auf Mobile
    'pattern_limit_mobile': 20  # Max Patterns auf Mobile anzeigen
}
# endregion

# ==============================================================================
# region               🔧 UTILITY FUNKTIONEN
# ==============================================================================
def get_exchange_config(exchange_name: str) -> Dict:
    """Holt Konfiguration für spezifischen Exchange"""
    return EXCHANGE_CONFIG.get(exchange_name, {})

def get_enabled_patterns() -> List[str]:
    """Gibt Liste der aktivierten Pattern zurück"""
    return PATTERN_CONFIG['candlestick_patterns']

def is_debug_mode() -> bool:
    """Prüft ob Debug-Modus aktiv"""
    return DEV_CONFIG['debug_mode']
# endregion
