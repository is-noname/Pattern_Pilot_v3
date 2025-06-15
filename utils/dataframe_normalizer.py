# utils/dataframe_normalizer.py - DATETIME CLEANUP VERSION
import pandas as pd
from typing import Dict, Any, Optional


# 📈 DataFrame-Normalisierung für Pattern Pilot
# ==============================================
#
# 🎯 Zweck:
# Dieses Modul stellt zentrale Normalisierungsfunktionen bereit, die
# von verschiedenen Komponenten für unterschiedliche Anwendungsfälle
# verwendet werden.
#
# ⚠️ WICHTIG: Zwei verschiedene Einstiegspunkte
# ----------------------------------------------
# Das System verwendet bewusst zwei verschiedene Normalisierungspfade:
#
# 1️⃣ normalize_api_result()
#    - Für vollständige API-Responses mit Metadaten
#    - Wird von api_manager.normalize_for_patterns() aufgerufen
#    - Setzt pattern_ready=True Flag in Metadaten
#    - Optimiert für strukturierte Daten aus APIs und Cache
#
# 2️⃣ normalize_dataframe_for_patterns()
#    - Für reine DataFrames ohne Metadaten-Kontext
#    - Wird von patterns.prepare_dataframe_for_patterns() aufgerufen
#    - Detailliertere Debug-Ausgaben (verbose=True)
#    - Optimiert für direkte Verwendung in Pattern-Detektoren
#
# 🔄 Gemeinsamer Kern:
# Beide Pfade verwenden die gleiche Grundlogik zur Normalisierung:
# - Integer-Index (0,1,2,...) für iloc-Zugriff
# - 'datetime' als Spalte für Zeitreferenz (GEÄNDERT von 'date')
# - Sortierung nach Zeit
# - Numerische OHLCV-Spalten
# - Entfernung von NaN-Werten in wichtigen Spalten
#
# 📝 Beispiele:
# ```python
# # Für API-Responses (mit Metadaten):
# result = api_manager.normalize_for_patterns(api_response)
#
# # Für reine DataFrames (ohne Metadaten):
# df_ready = patterns.prepare_dataframe_for_patterns(raw_df)


def normalize_dataframe_for_patterns(df, verbose=False):
    """
    Zentrale Normalisierungsfunktion für technische Pattern-Erkennung - DATETIME VERSION

    Stellt sicher:
    1. Integer-Index (0,1,2,...) für iloc-Zugriff
    2. 'datetime' als Spalte für Zeitreferenz
    3. Sortierung nach Zeit
    4. Numerische OHLCV-Spalten
    5. Keine NaN-Werte in wichtigen Spalten
    """
    if df.empty:
        return df

    working_df = df.copy()

    # 1. DatetimeIndex zu 'datetime' Column + Integer-Index
    if isinstance(working_df.index, pd.DatetimeIndex):
        if 'datetime' not in working_df.columns:
            working_df['datetime'] = working_df.index
        working_df = working_df.reset_index(drop=True)
        if verbose: print("🔧 DatetimeIndex → Integer-Index + datetime Column")

    # Handle legacy 'date' column → 'datetime'
    if 'date' in working_df.columns and 'datetime' not in working_df.columns:
        working_df = working_df.rename(columns={'date': 'datetime'})
        if verbose: print("🔧 Legacy 'date' → 'datetime' column")

    # 2. Datetime-Format und Sortierung sicherstellen
    if 'datetime' in working_df.columns:
        working_df['datetime'] = pd.to_datetime(working_df['datetime'], errors='coerce')
        working_df = working_df.sort_values('datetime').reset_index(drop=True)

    # 3. Numerische Spalten sicherstellen
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in working_df.columns:
            working_df[col] = pd.to_numeric(working_df[col], errors='coerce')

    # 4. NaN-Werte in wichtigen Spalten entfernen
    essential_cols = ['open', 'high', 'low', 'close']
    available_cols = [col for col in essential_cols if col in working_df.columns]
    if available_cols:
        working_df = working_df.dropna(subset=available_cols)

    if verbose: print(f"📊 DataFrame normalisiert: {len(working_df)} Zeilen")
    return working_df


def normalize_api_result(result: Dict[str, Any], verbose=False) -> Dict[str, Any]:
    """Wrapper für API-Ergebnisse"""
    if result['data'].empty:
        return result

    result_copy = result.copy()
    result_copy['data'] = normalize_dataframe_for_patterns(result['data'], verbose)
    result_copy['metadata']['pattern_ready'] = True
    return result_copy