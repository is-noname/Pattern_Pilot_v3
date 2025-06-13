# cache/__init__.py
"""
Cache-System für Krypto-OHLCV-Daten
"""
import self as self

from .cache_manager import CryptoDataCache, cache_instance

# Globale Instanz erstellen
# aktuell keine

__all__ = ['CryptoDataCache', 'cache_instance']

print(f"[CACHE] Cache-Modul geladen: {id(cache_instance)}")
