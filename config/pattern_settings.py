# config/pattern_settings.py



# Generelle Einstellungen
PATTERN_ACTIVE_DEFAULT = True  # Alle Patterns standardmäßig aktiv

# ==============================================================================
#                      Pattern Styles
# ==============================================================================


# ==============================================================================
#                      Pattern Detection
# ==============================================================================
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
    "macd_cross": { # in TIMEFRAME_CONFIGS aber nicht angepasst
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
    "bb_squeeze": { # in TIMEFRAME_CONFIGS aber nicht angepasst
        "active": True,
        "compression_threshold": 0.8,  # BB-Breite unter 80% des MA
        "reliability": 8
    },
    # Weitere Indikator Patterns...
}

# ==============================================================================
#                      Pattern Multi Timeframe Pattern Configs
# ==============================================================================
'''
Pattern Detection Configs per timeframe
'''
# Multi Timeframe Pattern Configs: neu importiert ist in Implementierungsvorbereitung
TIMEFRAME_CONFIGS = {
    # ==============================================================================
    #                      1 Day
    # ==============================================================================
    "1d": {
"doji": {
        "active": True, "body_size_threshold": 0.05, "min_shadow_ratio": 2.0, "reliability": 6},
        # •••••••••••••••••••••••••• Chart Patterns •••••••••••••••••••••••••• #
        "double_bottom": {"active": True, "tolerance": 0.03, "lookback_periods": 5, "min_pattern_bars": 5},
        "double_top": {"tolerance": 0.03, "lookback_periods": 5, "min_pattern_bars": 5},
        "head_and_shoulders": {"tolerance": 0.025, "lookback_periods": 5, "min_pattern_bars": 10},
        "inverse_head_and_shoulders": {"tolerance": 0.025, "lookback_periods": 5, "min_pattern_bars": 10},
        "ascending_triangle": {"lookback_periods": 5, "min_touches": 2, "min_pattern_bars": 10},
        "descending_triangle": {"lookback_periods": 5, "min_touches": 2, "min_pattern_bars": 10},
        "symmetrical_triangle": {"lookback_periods": 5, "min_touches": 2, "min_pattern_bars": 10},
        "falling_wedge": {"min_pattern_bars": 10, "min_touches": 2},
        "rising_wedge": {"min_pattern_bars": 10, "min_touches": 2}
    },
    # ==============================================================================
    #                      3 Days
    # ==============================================================================
    "3d": {
        # •••••••••••••••••••••••••• Chart Patterns •••••••••••••••••••••••••• #
        "double_bottom": {"tolerance": 0.04, "lookback_periods": 4, "min_pattern_bars": 4},
        "double_top": {"tolerance": 0.04, "lookback_periods": 4, "min_pattern_bars": 4},
        "head_and_shoulders": {"tolerance": 0.03, "lookback_periods": 4, "min_pattern_bars": 8},
        "inverse_head_and_shoulders": {"tolerance": 0.03, "lookback_periods": 4, "min_pattern_bars": 8},
        "ascending_triangle": {"lookback_periods": 4, "min_touches": 2, "min_pattern_bars": 8},
        "descending_triangle": {"lookback_periods": 4, "min_touches": 2, "min_pattern_bars": 8},
        "symmetrical_triangle": {"lookback_periods": 4, "min_touches": 2, "min_pattern_bars": 8},
        "falling_wedge": {"min_pattern_bars": 8, "min_touches": 2},
        "rising_wedge": {"min_pattern_bars": 8, "min_touches": 2}
    },
    # ==============================================================================
    #                      1 Week
    # ==============================================================================
    "1w": {
        # •••••••••••••••••••••••••• Chart Patterns •••••••••••••••••••••••••• #
        "double_bottom": {"tolerance": 0.05, "lookback_periods": 3, "min_pattern_bars": 3},
        "double_top": {"tolerance": 0.05, "lookback_periods": 3, "min_pattern_bars": 3},
        "head_and_shoulders": {"tolerance": 0.04, "lookback_periods": 3, "min_pattern_bars": 6},
        "inverse_head_and_shoulders": {"tolerance": 0.04, "lookback_periods": 3, "min_pattern_bars": 6},
        "ascending_triangle": {"lookback_periods": 3, "min_touches": 2, "min_pattern_bars": 6},
        "descending_triangle": {"lookback_periods": 3, "min_touches": 2, "min_pattern_bars": 6},
        "symmetrical_triangle": {"lookback_periods": 3, "min_touches": 2, "min_pattern_bars": 6},
        "falling_wedge": {"min_pattern_bars": 6, "min_touches": 2},
        "rising_wedge": {"min_pattern_bars": 6, "min_touches": 2}
    },
    # ==============================================================================
    #                      1 Month
    # ==============================================================================
    "1m": {

        # •••••••••••••••••••••••••• Chart Patterns •••••••••••••••••••••••••• #
        "double_bottom": {"tolerance": 0.07, "lookback_periods": 3, "min_pattern_bars": 3},
        "double_top": {"tolerance": 0.07, "lookback_periods": 3, "min_pattern_bars": 3},
        "head_and_shoulders": {"tolerance": 0.06, "lookback_periods": 3, "min_pattern_bars": 5},
        "inverse_head_and_shoulders": {"tolerance": 0.06, "lookback_periods": 3, "min_pattern_bars": 5},
        "ascending_triangle": {"lookback_periods": 3, "min_touches": 2, "min_pattern_bars": 5},
        "descending_triangle": {"lookback_periods": 3, "min_touches": 2, "min_pattern_bars": 5},
        "symmetrical_triangle": {"lookback_periods": 3, "min_touches": 2, "min_pattern_bars": 5},
        "falling_wedge": {"min_pattern_bars": 5, "min_touches": 2},
        "rising_wedge": {"min_pattern_bars": 5, "min_touches": 2}
    }
}

# Pattern-Erkennungs-Parameter  ++++ genutzt von double_patterns ++++
PATTERN_CONFIGS = {
    "double_bottom": {
        "tolerance": 0.03,      # Toleranz für ähnliche Preispunkte (3%)
        "lookback_periods": 5,  # Anzahl der Perioden für lokale Tiefs
        "min_pattern_bars": 5   # Mindestabstand zwischen den Tiefs
    },
    "double_top": {
        "tolerance": 0.03,
        "lookback_periods": 5,
        "min_pattern_bars": 5
    }
}