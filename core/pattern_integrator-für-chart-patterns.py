# core/pattern_integrator.py

from patterns.pattern_manager import pattern_manager
from core.market_engine import market_engine
from config.settings import PATTERN_CONFIG


def detect_advanced_patterns(
        symbol: str,
        timeframe: str = "1d",
        limit: int = 200,
        exchange: str = None,
        pattern_types: list = None,
        use_cache: bool = True
):
    """
    Erkennt komplexe Chart-Patterns wie Double Bottom, Head & Shoulders etc.
    Nutzt market_engine für OHLCV-Daten und pattern_manager für Analyse.

    Args:
        symbol: Trading Pair (z.B. "BTC/USDT")
        timeframe: Zeitrahmen (z.B. "1d", "4h")
        limit: Anzahl der Candles für Analyse
        exchange: Exchange-Name oder None für Auto-Routing
        pattern_types: Spezifische Pattern-Typen oder None für alle
        use_cache: Cache für wiederholte Analysen nutzen

    Returns:
        Dict mit erkannten Patterns nach Typ gruppiert
    """

    # •••••••••••••••••••••••••• 1. OHLCV-Daten von market_engine holen •••••••••••••••••••••••••• #
    df = market_engine.get_ohlcv(symbol, timeframe, limit, exchange)

    if df.empty:
        print(f"❌ Keine Daten für {symbol} verfügbar")
        return {}

    # •••••••••••••••••••••••••• 2. Sicherstellen, dass die Daten korrekt formatiert sind •••••••••••••••••••••••••• #
    # PatternManager erwartet möglicherweise eine 'date' Spalte statt 'datetime'
    if 'datetime' in df.columns and 'date' not in df.columns:
        df['date'] = df['datetime']

    # •••••••••••••••••••••••••• 3. Pattern-Typen festlegen •••••••••••••••••••••••••• #
    if pattern_types is None:
        # Alle in settings.py definierten Patterns verwenden
        pattern_types = PATTERN_CONFIG.get('advanced_patterns', [])

    # •••••••••••••••••••••••••• 4. PatternManager aufrufen •••••••••••••••••••••••••• #
    patterns = pattern_manager.detect_patterns(
        df=df,
        timeframe=timeframe,
        pattern_types=pattern_types,
        use_cache=use_cache,
        state=None  # State ist optional, aktuell nicht implementiert
    )

    # •••••••••••••••••••••••••• 5. Statistiken ausgeben •••••••••••••••••••••••••• #
    stats = pattern_manager.get_pattern_count(patterns)
    print(f"📊 Pattern-Analyse für {symbol} ({timeframe}):")
    print(f"   - {stats['total']} Patterns gefunden")
    print(f"   - {stats['bullish']} bullish, {stats['bearish']} bearish, {stats['neutral']} neutral")

    return patterns