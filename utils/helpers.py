import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os


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


def calculate_percent_change(current, previous):
    """Berechnet prozentuale Änderung"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100


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


def create_output_dir(dirname="output"):
    """Erstellt ein Ausgabeverzeichnis, falls es nicht existiert"""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return dirname


def resample_ohlcv(df, interval='1D'):
    """
    Resampled OHLCV-Daten auf einen anderen Zeitraum

    Args:
        df: DataFrame mit OHLCV-Daten und 'date' Spalte
        interval: Ziel-Intervall ('1D', '1W', '1M', etc.)
    """
    # Stelle sicher, dass es einen Index gibt
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.set_index('date')

    resampled = df.resample(interval).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum' if 'volume' in df.columns else None
    })

    return resampled.reset_index()


def normalize_ohlcv_data(df):
    """
    Normalisiert OHLCV-Daten in ein Standardformat

    Args:
        df: DataFrame mit Preisdaten

    Returns:
        Normalisiertes DataFrame mit 'date', 'open', 'high', 'low', 'close', 'volume'
    """
    # Prüfen, ob die nötigen Spalten vorhanden sind
    required_columns = ['date', 'open', 'high', 'low', 'close']

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

            if not found and req_col != 'volume':  # Volumen ist optional
                raise ValueError(f"Erforderliche Spalte '{req_col}' fehlt im DataFrame")

    # Spalten umbenennen, falls nötig
    if mapping and any(k != v for k, v in mapping.items()):
        df = df.rename(columns=mapping)

    # Stelle sicher, dass date ein datetime ist
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])

    # Stelle sicher, dass numerische Spalten auch wirklich numerisch sind
    numeric_columns = ['open', 'high', 'low', 'close']
    if 'volume' in df.columns:
        numeric_columns.append('volume')

    for col in numeric_columns:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df