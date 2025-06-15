# pattern_categories.py
# Hierarchische Pattern-Kategorisierung

PATTERN_CATEGORIES = {
    # 1. Trendumkehrmuster
    "trend_reversal": {
        "bullish": ["double_bottom", "inverse_head_and_shoulders", "rounding_bottom", "triple_bottom", "v_pattern"],
        # v_bottom -> v_pattern
        "bearish": ["double_top", "head_and_shoulders", "rounding_top", "triple_top", "v_pattern"]  # v_top -> v_pattern
    },

    # 2. Trendfortsetzungsmuster
    "trend_continuation": {
        "bullish": ["ascending_triangle", "bullish_flag", "bullish_pennant", "bullish_rectangle"],
        "bearish": ["descending_triangle", "bearish_flag", "bearish_pennant", "bearish_rectangle"],
        "neutral": ["symmetrical_triangle", "upward_channel", "downward_channel"]
        # lateral_channel -> upward_channel, downward_channel
    },

    # 3. Komplexe Muster (entferne fehlende)
    "complex": {
        "bullish": ["cup_and_handle", "falling_wedge"],
        "bearish": ["rising_wedge"],  # dead_cat_bounce entfernt
        "neutral": []  # elliott_wave und three_drives entfernt
    }
}

# Flache Listen für einfache Filterung
ALL_BULLISH = (PATTERN_CATEGORIES["trend_reversal"]["bullish"] + 
               PATTERN_CATEGORIES["trend_continuation"]["bullish"] + 
               PATTERN_CATEGORIES["complex"]["bullish"])

ALL_BEARISH = (PATTERN_CATEGORIES["trend_reversal"]["bearish"] + 
               PATTERN_CATEGORIES["trend_continuation"]["bearish"] + 
               PATTERN_CATEGORIES["complex"]["bearish"])

ALL_NEUTRAL = (PATTERN_CATEGORIES["trend_continuation"]["neutral"] + 
               PATTERN_CATEGORIES["complex"]["neutral"])

ALL_COMPLEX = (PATTERN_CATEGORIES["complex"]["bullish"] + 
               PATTERN_CATEGORIES["complex"]["bearish"] + 
               PATTERN_CATEGORIES["complex"]["neutral"])
