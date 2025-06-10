# config/settings.py - ZENTRALE KONFIGURATION - Settings für Pattern Pilot
import os
from typing import Dict, List


#==============================================================================
# region               📡 EXCHANGE KONFIGURATION
#==============================================================================
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
    }
}
# endregion

#==============================================================================
# region               📊 CHART KONFIGURATION
#==============================================================================
CHART_CONFIG = {
    'default_candles': 200,
    'max_candles': 1000,
    'default_timeframe': "1d",
    'theme': 'plotly_dark',
    'height': 800,
    'colors': {
        'bullish': '#00ff88',
        'bearish': '#ff4444',
        'neutral': '#ffaa00',
        'background': '#0e1117'
    }
}
# endregion

#==============================================================================
# region                🎯 PATTERN KONFIGURATION
#==============================================================================
PATTERN_CONFIG = {
    # Welche Candlestick-Pattern aktivieren
    'candlestick_patterns': [
        'doji', 'hammer', 'hanging_man', 'shooting_star',
        'engulfing_bullish', 'morning_star', 'evening_star',
        'three_white_soldiers', 'three_black_crows',
        'harami', 'piercing', 'dark_cloud'
    ],
    
    # Custom Pattern Settings
    'bollinger_periods': 20,
    'ma_fast_period': 20,
    'ma_slow_period': 50,
    'rsi_period': 14,
    
    # Minimum pattern strength to display
    'min_pattern_strength': 0.5,

    # 🎨 Chart Pattern Visualisierung
    'pattern_styles': {
        'doji': {'symbol': 'circle', 'color': '#117e23', 'size': 3, 'emoji': '🎯'},
        'hammer': {'symbol': 'triangle-up', 'color': '#00ff88', 'size': 4, 'emoji': '🔨'},
        'engulfing': {'symbol': 'star', 'color': '#ff0080', 'size': 5, 'emoji': '🌟'},
        'ma_crossover': {'symbol': 'diamond', 'color': '#00aaff', 'size': 4, 'emoji': '💎'},
        'support_resistance': {'symbol': 'square', 'color': '#aa00ff', 'size': 3, 'emoji': '🔷'},
        'hanging_man': {'symbol': 'triangle-down', 'color': '#ff4444', 'size': 4, 'emoji': '⚠️'},
        'shooting_star': {'symbol': 'star-triangle-up', 'color': '#ff6600', 'size': 4, 'emoji': '⭐'},
        'morning_star': {'symbol': 'star-square', 'color': '#66ff66', 'size': 4, 'emoji': '🌅'},
        'evening_star': {'symbol': 'star-diamond', 'color': '#ff3366', 'size': 4, 'emoji': '🌆'},
        'three_white_soldiers': {'symbol': 'arrow-up', 'color': '#44ff44', 'size': 5, 'emoji': '⬆️'},
        'three_black_crows': {'symbol': 'arrow-down', 'color': '#ff4444', 'size': 5, 'emoji': '⬇️'},
        'harami': {'symbol': 'hourglass', 'color': '#ffaa44', 'size': 3, 'emoji': '⏳', 'line': {'width': 0.5, 'color': 'black'}},
        'piercing': {'symbol': 'triangle-up-open', 'color': '#44aa44', 'size': 4, 'emoji': '🔺'},
        'dark_cloud': {'symbol': 'triangle-down-open', 'color': '#aa4444', 'size': 4, 'emoji': '🔻'},
        # Neue Pattern-Styles
        'inverted_hammer': {'symbol': 'triangle-up-open', 'color': '#ff9900', 'size': 4, 'emoji': '🔨'},
        'marubozu': {'symbol': 'diamond', 'color': '#00ffcc', 'size': 4, 'emoji': '📊'},
        'spinning_top': {'symbol': 'circle-open', 'color': '#aaaaaa', 'size': 3, 'emoji': '🔄'},
        'dragonfly_doji': {'symbol': 'triangle-down-dot', 'color': '#33ccff', 'size': 4, 'emoji': '🐉'},
        'kicking': {'symbol': 'x', 'color': '#ff3366', 'size': 5, 'emoji': '👟'},
        'tasuki_gap': {'symbol': 'diamond-tall', 'color': '#66ff66', 'size': 4, 'emoji': '🧩'},
        'breakaway': {'symbol': 'star-diamond', 'color': '#ff6600', 'size': 5, 'emoji': '💥'},
        'doji_star': {'symbol': 'star', 'color': '#ffff00', 'size': 4, 'emoji': '⭐'},
    }
}
# endregion

#==============================================================================
# region              💾 CACHE KONFIGURATION
#==============================================================================
CACHE_CONFIG = {
    'enabled': True,
    'ttl_seconds': 300,  # 5 Minuten
    'type': 'memory',    # 'memory' oder 'redis'
    'redis_url': 'redis://localhost:6379/0'
}
# endregion

#==============================================================================
# region               🎨 UI KONFIGURATION
#==============================================================================
UI_CONFIG = {
    'page_title': 'Pattern Pilot v2',
    'page_icon': '🚀',
    'layout': 'wide',
    'sidebar_width': 300,
    'default_symbols': [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT',
        'SOL/USDT', 'MATIC/USDT', 'DOT/USDT', 'LINK/USDT'
    ],
    'default_timeframes': ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
}
# endregion

#==============================================================================
# region               🔧 DEVELOPMENT SETTINGS
#==============================================================================
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

#==============================================================================
# region               🔧 UTILITY FUNKTIONEN
#==============================================================================
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
