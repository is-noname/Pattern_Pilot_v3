import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os


# •••••••••••••••••••••••••• Preisformatierung für Anzeige •••••••••••••••••••••••••• #
def format_price(price, decimals=None):
    """
    Formatiert Preise für die Anzeige

    Args:
        price: Der zu formatierende Preis
        decimals: Anzahl der Dezimalstellen (auto wenn None)
    """
    if price is None:
        return "N/A"

    # Konvertiere String zu float, falls nötig
    try:
        price = float(price)
    except (TypeError, ValueError):
        return str(price)  # Wenn Konvertierung fehlschlägt, gib den Original-String zurück

    # Automatische Dezimalstellen basierend auf Preisgröße
    if decimals is None:
        if price < 0.0001:
            decimals = 8
        elif price < 0.01:
            decimals = 6
        elif price < 1:
            decimals = 4
        elif price < 1000:
            decimals = 2
        else:
            decimals = 0

    return f"{price:,.{decimals}f}"


# •••••••••••••••••••••••••• CALC: Prozentuale Änderung  •••••••••••••••••••••••••• #
def calculate_percent_change(current, previous):
    """Berechnet prozentuale Änderung"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100


# •••••••••••••••••••••••••• PROOF: Ist String ein ültiges Datum? •••••••••••••••••••••••••• #
def is_valid_date_format(date_str):
    """Überprüft, ob der String ein gültiges Datum ist"""
    try:
        if '-' in date_str:
            datetime.strptime(date_str, '%Y-%m-%d')
        elif '/' in date_str:
            datetime.strptime(date_str, '%Y/%m/%d')
        else:
            return False
        return True
    except:
        return False


# •••••••••••••••••••••••••• OPTIONAL: Erstellt ein Ausgabeverzeichnis •••••••••••••••••••••••••• #
def create_output_dir(dirname="output"):
    """Erstellt ein Ausgabeverzeichnis, falls es nicht existiert"""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return dirname


# •••••••••••••••••••••••••• RESAMPLE: OHLCV-Daten auf einen anderen Zeitraum •••••••••••••••••••••••••• #
def resample_ohlcv(df, interval='1D'):
    """
    Resamples OHLCV-Daten auf einen anderen Zeitraum - DATETIME CLEANUP

    Args:
        df: DataFrame mit OHLCV-Daten und 'datetime' Spalte
        interval: Ziel-Intervall ('1D', '1W', '1M', etc.)

    Returns:
        DataFrame mit resampled Daten, 'datetime' als Spalte beibehalten
    """
    # Ensure datetime column exists
    if 'datetime' not in df.columns:
        raise ValueError("DataFrame muss 'datetime' column haben")

    # Work with datetime as column throughout - NO INDEX SWITCHING
    df_copy = df.copy()

    # Ensure datetime is proper type
    df_copy['datetime'] = pd.to_datetime(df_copy['datetime'])

    # Sort by datetime
    df_copy = df_copy.sort_values('datetime')

    # Set datetime as index temporarily for resampling ONLY
    df_indexed = df_copy.set_index('datetime')

    # Resample operations
    resampled = df_indexed.resample(interval).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum' if 'volume' in df.columns else 'first'
    })

    # Immediately reset index back to column
    result = resampled.reset_index()

    # Drop NaN rows that might result from resampling
    result = result.dropna(subset=['open', 'high', 'low', 'close'])

    return result


# •••••••••••••••••••••••••• NORMALIZE: OHLCV-Daten in Standardformat •••••••••••••••••••••••••• #
def normalize_ohlcv_data(df):
    """
    Normalisiert OHLCV-Daten in Standardformat - DATETIME CLEANUP

    Args:
        df: DataFrame mit Preisdaten

    Returns:
        Normalisiertes DataFrame mit 'datetime', 'open', 'high', 'low', 'close', 'volume'
    """
    # Prüfen, ob die nötigen Spalten vorhanden sind
    required_columns = ['datetime', 'open', 'high', 'low', 'close']

    # Spaltenübereinstimmung prüfen (case-insensitive)
    df_columns_lower = [col.lower() for col in df.columns]
    mapping = {}

    for req_col in required_columns:
        if req_col in df.columns:
            mapping[req_col] = req_col
        else:
            # Versuche, die Spalte mit passendem Namen zu finden
            found = False
            for col in df.columns:
                if col.lower() == req_col.lower():
                    mapping[req_col] = col
                    found = True
                    break
                # Special case: 'date' → 'datetime' mapping
                elif col.lower() == 'date' and req_col == 'datetime':
                    mapping[req_col] = col
                    found = True
                    break

            if not found and req_col != 'volume':  # Volumen ist optional
                raise ValueError(f"Erforderliche Spalte '{req_col}' fehlt im DataFrame")

    # Spalten umbenennen, falls nötig
    if mapping and any(k != v for k, v in mapping.items()):
        df = df.rename(columns=mapping)

    # Stelle sicher, dass datetime ein datetime ist
    if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
        df['datetime'] = pd.to_datetime(df['datetime'])

    # Stelle sicher, dass numerische Spalten auch wirklich numerisch sind
    numeric_columns = ['open', 'high', 'low', 'close']
    if 'volume' in df.columns:
        numeric_columns.append('volume')

    for col in numeric_columns:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# •••••••••••••••••••••••••• PREPARE. Patterns für Charts •••••••••••••••••••••••••• #
def prepare_patterns_for_chart(patterns, df):
    """Konvertiert Pattern-Indices zu Chart-ready Format"""
    INDEX_KEYS = ['left_shoulder', 'head', 'right_shoulder', 'left_bottom', 'right_bottom',
                  'breakout_idx', 'left_trough', 'right_trough']

    for pattern_list in patterns.values():
        for pattern in pattern_list:
            for key in INDEX_KEYS:
                if key in pattern and isinstance(pattern[key], int):
                    pattern[f"{key}_datetime"] = df['datetime'].iloc[pattern[key]]