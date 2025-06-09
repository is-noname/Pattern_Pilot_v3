# config/settings.py - Zentrale Konfiguration
import os
from typing import Dict, List

# 📡 Exchange Konfiguration
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

# 🎯 Pattern Konfiguration  
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
        'doji': {'symbol': 'circle', 'color': '#ffaa00', 'size': 12, 'emoji': '🎯'},
        'hammer': {'symbol': 'triangle-up', 'color': '#00ff88', 'size': 15, 'emoji': '🔨'},
        'engulfing': {'symbol': 'star', 'color': '#ff0080', 'size': 18, 'emoji': '🌟'},
        'ma_crossover': {'symbol': 'diamond', 'color': '#00aaff', 'size': 14, 'emoji': '💎'},
        'support_resistance': {'symbol': 'square', 'color': '#aa00ff', 'size': 10, 'emoji': '🔷'},
        'hanging_man': {'symbol': 'triangle-down', 'color': '#ff4444', 'size': 15, 'emoji': '⚠️'},
        'shooting_star': {'symbol': 'star-triangle-up', 'color': '#ff6600', 'size': 16, 'emoji': '⭐'},
        'morning_star': {'symbol': 'star-square', 'color': '#66ff66', 'size': 17, 'emoji': '🌅'},
        'evening_star': {'symbol': 'star-diamond', 'color': '#ff3366', 'size': 17, 'emoji': '🌆'},
        'three_white_soldiers': {'symbol': 'arrow-up', 'color': '#44ff44', 'size': 20, 'emoji': '⬆️'},
        'three_black_crows': {'symbol': 'arrow-down', 'color': '#ff4444', 'size': 20, 'emoji': '⬇️'},
        'harami': {'symbol': 'hourglass', 'color': '#ffaa44', 'size': 13, 'emoji': '⏳'},
        'piercing': {'symbol': 'triangle-up-open', 'color': '#44aa44', 'size': 14, 'emoji': '🔺'},
        'dark_cloud': {'symbol': 'triangle-down-open', 'color': '#aa4444', 'size': 14, 'emoji': '🔻'},
    }
}

# 💾 Cache Konfiguration
CACHE_CONFIG = {
    'enabled': True,
    'ttl_seconds': 300,  # 5 Minuten
    'type': 'memory',    # 'memory' oder 'redis'
    'redis_url': 'redis://localhost:6379/0'
}

# 📊 Chart Konfiguration
CHART_CONFIG = {
    'default_candles': 200,
    'max_candles': 1000,
    'theme': 'plotly_dark',
    'height': 800,
    'colors': {
        'bullish': '#00ff88',
        'bearish': '#ff4444', 
        'neutral': '#ffaa00',
        'background': '#0e1117'
    }
}

# 🎨 UI Konfiguration
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

# 🔧 Development Settings
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

# Utility Functions
def get_exchange_config(exchange_name: str) -> Dict:
    """Holt Konfiguration für spezifischen Exchange"""
    return EXCHANGE_CONFIG.get(exchange_name, {})

def get_enabled_patterns() -> List[str]:
    """Gibt Liste der aktivierten Pattern zurück"""
    return PATTERN_CONFIG['candlestick_patterns']

def is_debug_mode() -> bool:
    """Prüft ob Debug-Modus aktiv"""
    return DEV_CONFIG['debug_mode']