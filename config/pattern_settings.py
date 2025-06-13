# config/pattern_settings.py



# Generelle Einstellungen
PATTERN_ACTIVE_DEFAULT = True  # Alle Patterns standardmäßig aktiv

# Candlestick Patterns
CANDLESTICK = {
    "doji": {
        "active": True,
        "body_size_threshold": 0.05,  # Körper max 5% des Gesamtbereichs
        "min_shadow_ratio": 2.0,      # Min Verhältnis Schatten zu Körper
        "reliability": 6              # Zuverlässigkeit 1-10
    },
    "engulfing": {
        "active": True,
        "min_size_ratio": 1.5,        # Zweite Kerze mind. 1.5x erste Kerze
        "reliability": 8
    },
    # Weitere Candlestick Patterns...
}

# Indikator-basierte Patterns
INDICATOR = {
    "macd_cross": {
        "active": True,
        "signal_line": 0,             # Nulllinie für Crossover
        "min_histogram_change": 0.1,  # Minimale Änderung für Signal
        "reliability": 7
    },
    "rsi_extreme": {
        "active": True,
        "oversold": 30,
        "overbought": 70,
        "reliability": 6
    },
    "bb_squeeze": {
        "active": True,
        "compression_threshold": 0.8,  # BB-Breite unter 80% des MA
        "reliability": 8
    },
    # Weitere Indikator Patterns...
}


