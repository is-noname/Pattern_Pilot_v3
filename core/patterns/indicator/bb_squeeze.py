# patterns/indicator/bb_squeeze.py
from config.pattern_settings import INDICATOR

# Pattern-Infos
NAME = "Bollinger Band Squeeze"
DESCRIPTION = "Bollinger Bands verengen sich, deutet auf Volatilitätsausbruch hin"
TYPE = "Momentum"

# Settings aus pattern_settings.py holen
settings = INDICATOR["bb_squeeze"]


def detect_bb_squeeze(df, ):
    """Erkennt Bollinger Band Squeeze Pattern

    Args:
        df: DataFrame mit OHLCV-Daten und BB-Indikatoren

    Returns:
        Liste mit Signalen {timestamp, price, direction, pattern_name}
    """
    signals = []

    # Prüfen ob Pattern aktiviert ist
    if not settings["active"]:
        return signals

    # Voraussetzung: BB, BB-width und BB-width-MA wurden bereits berechnet
    if 'bb_upper' not in df.columns or 'bb_width' not in df.columns:
        return signals

    # Pattern-Erkennung
    for i in range(5, len(df)):
        # Hier nutzen wir den Wert aus den Settings statt Magic Number
        if (df['bb_width'].iloc[i] < df['bb_width_ma'].iloc[i] * settings["compression_threshold"]):
            # Weitere Bedingungen...
            signals.append({
                'timestamp': df.index[i],
                'price': df['close'].iloc[i],
                'direction': 'neutral',  # Squeeze ist richtungsneutral
                'pattern_name': NAME,
                'reliability': settings["reliability"]
            })

    return signals