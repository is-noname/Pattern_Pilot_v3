# patterns/__init__.py - FIXED VERSION
import pandas as pd

from core.patterns.formation_patterns import render_double_bottom_plotly
from core.patterns.formation_patterns.double_patterns import detect_double_bottom, detect_double_top, render_double_bottom, render_double_top
from core.patterns.formation_patterns.head_shoulders import detect_head_and_shoulders, detect_inverse_head_and_shoulders, render_head_and_shoulders_plotly, \
    render_inverse_head_and_shoulders_plotly
from core.patterns.formation_patterns.triple_patterns import detect_triple_top, detect_triple_bottom, render_triple_top, render_triple_bottom
from core.patterns.formation_patterns.triangles import detect_ascending_triangle, detect_descending_triangle, detect_symmetrical_triangle, \
    render_ascending_triangle, render_descending_triangle, render_symmetrical_triangle
from core.patterns.formation_patterns.flags import detect_bullish_flag, detect_bearish_flag, detect_bullish_pennant, detect_bearish_pennant, \
    render_bullish_flag, render_bearish_flag, render_bullish_pennant, render_bearish_pennant
from core.patterns.formation_patterns.wedges import detect_falling_wedge, detect_rising_wedge, render_falling_wedge, render_rising_wedge
from core.patterns.formation_patterns.rectangles import detect_bullish_rectangle, detect_bearish_rectangle, render_bullish_rectangle, \
    render_bearish_rectangle
from core.patterns.formation_patterns.channels import detect_upward_channel, detect_downward_channel, render_upward_channel, render_downward_channel
from core.patterns.formation_patterns.gaps import detect_breakaway_gap, detect_runaway_gap, detect_exhaustion_gap, detect_common_gap, render_common_gap, \
    render_exhaustion_gap, render_runaway_gap, render_breakaway_gap
from core.patterns.formation_patterns.rounding_patterns import detect_rounding_bottom, detect_rounding_top, render_rounding_bottom, render_rounding_top
from core.patterns.formation_patterns.v_cup_patterns import detect_v_pattern, detect_cup_and_handle, render_v_pattern, render_cup_and_handle
from core.patterns.formation_patterns.diamond_patterns import detect_diamond_top, detect_diamond_bottom, render_diamond_top, render_diamond_bottom
from config.pattern_settings import TIMEFRAME_CONFIGS
from utils.pattern_strength import calculate_pattern_strength


def get_pattern_config(pattern_name, config=None, timeframe="1d"):
    """Holt timeframe-spezifische Konfiguration für ein Muster"""
    if timeframe in TIMEFRAME_CONFIGS and pattern_name in TIMEFRAME_CONFIGS[timeframe]:
        base_config = config or {}
        timeframe_config = TIMEFRAME_CONFIGS[timeframe][pattern_name]
        return {**base_config, **timeframe_config}
    return config


# Registriere alle verfügbaren Pattern-Detektoren
PATTERN_DETECTORS = {
    "double_bottom": detect_double_bottom,
    "double_top": detect_double_top,
    "head_and_shoulders": detect_head_and_shoulders,
    "inverse_head_and_shoulders": detect_inverse_head_and_shoulders,
    "triple_top": detect_triple_top,
    "triple_bottom": detect_triple_bottom,
    "ascending_triangle": detect_ascending_triangle,
    "descending_triangle": detect_descending_triangle,
    "symmetrical_triangle": detect_symmetrical_triangle,
    "bullish_flag": detect_bullish_flag,
    "bearish_flag": detect_bearish_flag,
    "bullish_pennant": detect_bullish_pennant,
    "bearish_pennant": detect_bearish_pennant,
    "bullish_rectangle": detect_bullish_rectangle,
    "bearish_rectangle": detect_bearish_rectangle,
    "upward_channel": detect_upward_channel,
    "downward_channel": detect_downward_channel,
    "breakaway_gap": detect_breakaway_gap,
    "runaway_gap": detect_runaway_gap,
    "exhaustion_gap": detect_exhaustion_gap,
    "common_gap": detect_common_gap,
    "falling_wedge": detect_falling_wedge,
    "rising_wedge": detect_rising_wedge,
    "rounding_bottom": detect_rounding_bottom,
    "rounding_top": detect_rounding_top,
    "v_pattern": detect_v_pattern,
    "cup_and_handle": detect_cup_and_handle,
    "diamond_top": detect_diamond_top,
    "diamond_bottom": detect_diamond_bottom
}

PATTERN_RENDERERS = {
    "double_bottom": render_double_bottom_plotly,
    "double_top": render_double_top,
    "head_and_shoulders": render_head_and_shoulders_plotly,
    "inverse_head_and_shoulders": render_inverse_head_and_shoulders_plotly,
    "triple_top": render_triple_top,
    "triple_bottom": render_triple_bottom,
    "ascending_triangle": render_ascending_triangle,
    "descending_triangle": render_descending_triangle,
    "symmetrical_triangle": render_symmetrical_triangle,
    "bullish_flag": render_bullish_flag,
    "bearish_flag": render_bearish_flag,
    "bullish_pennant": render_bullish_pennant,
    "bearish_pennant": render_bearish_pennant,
    "bullish_rectangle": render_bullish_rectangle,
    "bearish_rectangle": render_bearish_rectangle,
    "upward_channel": render_upward_channel,
    "downward_channel": render_downward_channel,
    "breakaway_gap": render_breakaway_gap,
    "runaway_gap": render_runaway_gap,
    "exhaustion_gap": render_exhaustion_gap,
    "common_gap": render_common_gap,
    "falling_wedge": render_falling_wedge,
    "rising_wedge": render_rising_wedge,
    "rounding_bottom": render_rounding_bottom,
    "rounding_top": render_rounding_top,
    "v_pattern": render_v_pattern,
    "cup_and_handle": render_cup_and_handle,
    "diamond_top": render_diamond_top,
    "diamond_bottom": render_diamond_bottom
}


def detect_all_patterns(df, timeframe="1d", state=None):
    """
    🔧 FIXED: Führt alle Mustererkennungen aus mit korrektem Index-Management

    Pattern-Detektoren erwarten:
    - Integer-Index (0,1,2,3...) für iloc-Zugriff
    - 'date' Column für Zeitinformationen
    """
    print(f"🔍 Pattern Detection für {len(df)} Datenpunkte ({timeframe})")

    # Prüfen ob DataFrame bereits pattern_ready ist
    is_pattern_ready = df.attrs.get('pattern_ready', False)

    # Nur normalisieren, wenn nötig
    working_df = df if is_pattern_ready else prepare_dataframe_for_patterns(df)

    if working_df.empty:
        print("❌ Leerer DataFrame - keine Pattern Detection möglich")
        return {}

    print(f"✅ DataFrame vorbereitet: Index={type(working_df.index)}, Shape={working_df.shape}")

    results = {}
    successful_patterns = 0

    for pattern_name, detector_func in PATTERN_DETECTORS.items():
        try:
            # Timeframe-spezifische Konfiguration
            config = get_pattern_config(pattern_name, None, timeframe)

            # Pattern Detection mit sicherem DataFrame
            patterns = detector_func(working_df, config, timeframe)

            # Stärke berechnen falls State verfügbar
            if state is not None and patterns:
                for pattern in patterns:
                    try:
                        pattern['strength'] = calculate_pattern_strength(
                            pattern, pattern_name, working_df, timeframe, state
                        )
                    except Exception as e:
                        print(f"⚠️ Stärkeberechnung für {pattern_name} fehlgeschlagen: {e}")
                        pattern['strength'] = 0.5  # Fallback

            results[pattern_name] = patterns

            if patterns:
                successful_patterns += len(patterns)
                print(f"✅ {pattern_name}: {len(patterns)} Muster gefunden")

        except Exception as e:
            print(f"❌ Fehler bei {pattern_name}: {e}")
            import traceback
            traceback.print_exc()
            results[pattern_name] = []

    print(
        f"🎯 Pattern Detection abgeschlossen: {successful_patterns} Muster in {len([r for r in results.values() if r])} Kategorien")
    return results


def prepare_dataframe_for_patterns(df):
    """
    📊 DataFrame-Normalisierung für Pattern-Erkennung

    Bereitet REINE DataFrames für die Pattern-Erkennung vor.
    Im Gegensatz zu api_manager.normalize_for_patterns() arbeitet diese
    Funktion direkt mit DataFrame-Objekten ohne Metadaten-Kontext.

    ⚙️ Funktionsweise:
    - Aktiviert verbose=True für ausführliche Debug-Informationen
    - Delegiert an normalize_dataframe_for_patterns ohne Metadaten-Handling
    - Führt KEINE Duplikatsprüfung durch (immer vollständige Normalisierung)
    - Delegiert an die gemeinsame Normalisierungsfunktion in utils

    🔍 Spezifische Eigenschaften:
    - Optimiert für direkte DataFrame-Manipulation in Pattern-Detektoren
    - Ausführlichere Logging-Ausgaben zur Fehlersuche
    - Keine Prüfung auf vorherige Normalisierung (performance-intensiver)

    ⚠️ Hinweis:
    - Bei Daten aus API-Responses IMMER api_manager.normalize_for_patterns()
      verwenden, um Metadaten-Struktur zu erhalten!

    @param df: DataFrame mit OHLCV-Daten
    @return: Für Pattern-Erkennung optimiertes DataFrame
    """
    from utils.dataframe_normalizer import normalize_dataframe_for_patterns
    return normalize_dataframe_for_patterns(df, verbose=True)


# Debug-Funktion
def debug_dataframe_structure(df, context=""):
    """Debug-Hilfe für DataFrame-Struktur"""
    print(f"\n🔍 DataFrame Debug ({context}):")
    print(f"  Shape: {df.shape}")
    print(f"  Index Type: {type(df.index)}")
    print(f"  Index Range: {df.index[0] if len(df) > 0 else 'N/A'} bis {df.index[-1] if len(df) > 0 else 'N/A'}")
    print(f"  Columns: {df.columns.tolist()}")
    if 'date' in df.columns:
        print(f"  Date Range: {df['date'].min()} bis {df['date'].max()}")
    print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")