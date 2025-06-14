# ohlcv_test.py
# Test des OHLCV-Daten-Abrufs mit expliziter Wartezeit

import time
import os
import pandas as pd
from core.market_engine import MarketEngine

def test_ohlcv_with_wait():
    """Test des OHLCV-Daten-Abrufs mit expliziter Wartezeit"""
    print("🔍 OHLCV Test mit Wartezeit")
    
    # Cache-Datei suchen und bei Bedarf löschen
    print("\n1. Prüfe auf Cache-Datei...")
    cache_dirs = [
        "./.cache",
        "./cache",
        "./data/cache"
    ]
    
    cache_found = False
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            print(f"   Cache-Verzeichnis gefunden: {cache_dir}")
            # Nach sqlite oder JSON-Dateien suchen
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.sqlite') or f.endswith('.json')]
            if cache_files:
                cache_found = True
                print(f"   Cache-Dateien gefunden: {cache_files}")
                
                # Option zum Löschen des Caches
                delete_cache = True  # Bei Bedarf auf False setzen
                if delete_cache:
                    print("   Lösche Cache-Dateien...")
                    for file in cache_files:
                        try:
                            os.remove(os.path.join(cache_dir, file))
                            print(f"   ✅ Gelöscht: {file}")
                        except Exception as e:
                            print(f"   ❌ Fehler beim Löschen von {file}: {str(e)}")
    
    if not cache_found:
        print("   Keine Cache-Dateien gefunden")
    
    # MarketEngine initialisieren
    print("\n2. MarketEngine laden...")
    market_engine = MarketEngine()
    
    # Explizite Wartezeit für Exchange-Initialisierung
    wait_time = 30  # Sekunden
    print(f"\n3. Warte {wait_time} Sekunden auf Exchange-Initialisierung...")
    
    start_time = time.time()
    while time.time() - start_time < wait_time:
        # Status alle 5 Sekunden ausgeben
        if int(time.time() - start_time) % 5 == 0:
            online_exchanges = []
            loading_exchanges = []
            
            for name, exchange in market_engine.exchanges.items():
                if isinstance(exchange, dict):
                    loading_exchanges.append(name)
                else:
                    online_exchanges.append(name)
            
            print(f"   Wartezeit: {int(time.time() - start_time)}s - Online: {online_exchanges} - Loading: {loading_exchanges}")
            time.sleep(1)  # Kurze Pause, um nicht in jeder Iteration zu drucken
        else:
            time.sleep(0.1)
    
    # Nach der Wartezeit den Status ausgeben
    online_exchanges = []
    loading_exchanges = []
    
    for name, exchange in market_engine.exchanges.items():
        if isinstance(exchange, dict):
            loading_exchanges.append(name)
        else:
            online_exchanges.append(name)
    
    print(f"\n4. Nach {wait_time} Sekunden:")
    print(f"   Online Exchanges: {online_exchanges}")
    print(f"   Noch ladende Exchanges: {loading_exchanges}")
    
    # Symbol und Timeframe
    symbol = "BTC/USDT"
    timeframe = "1d"
    limit = 100
    
    # OHLCV-Daten für jede online Exchange testen
    print(f"\n5. OHLCV-Daten für {symbol} ({timeframe}) von allen online Exchanges testen...")
    
    for exchange_name in online_exchanges:
        try:
            print(f"\n   Testing {exchange_name}...")
            df = market_engine.get_ohlcv(symbol, timeframe, limit=limit, exchange=exchange_name)
            
            if df is not None and len(df) > 0:
                print(f"   ✅ Daten von {exchange_name} geladen: {len(df)} Datenpunkte")
                print(f"   DataFrame Spalten: {df.columns.tolist()}")
                print(f"   Erste 3 Datenpunkte:")
                print(df.head(3))
                
                # Patterns erkennen
                print(f"\n   Pattern-Erkennung für {exchange_name}-Daten...")
                try:
                    patterns = market_engine.detect_patterns(df)
                    print(f"   Pattern-Typ: {type(patterns)}")
                    print(f"   Pattern-Keys: {list(patterns.keys())}")
                    
                    if 'technical_indicators' in patterns:
                        ti = patterns['technical_indicators']
                        print(f"   Technical Indicators: {len(ti)} Typen")
                        print(f"   Technical Indicator Keys: {list(ti.keys())}")
                        
                        # Nach Doji suchen
                        if 'doji' in ti:
                            doji = ti['doji']
                            print(f"   Doji gefunden: {len(doji)} Signale")
                            
                            # Doji-Filter testen
                            try:
                                print(f"\n   Doji-Filter testen...")
                                filtered = market_engine.filter_patterns(
                                    patterns, 
                                    min_strength=0.0, 
                                    pattern_types=['doji']
                                )
                                
                                print(f"   Filter-Ergebnis: {type(filtered)}")
                                print(f"   Filter-Keys: {list(filtered.keys()) if isinstance(filtered, dict) else 'NOT DICT'}")
                                
                                if isinstance(filtered, dict) and 'technical_indicators' in filtered:
                                    ti_filtered = filtered['technical_indicators']
                                    if 'doji' in ti_filtered:
                                        print(f"   Doji nach Filter: {len(ti_filtered['doji'])} Signale")
                                    else:
                                        print("   ❌ Kein 'doji' nach Filter")
                            except Exception as e:
                                print(f"   ❌ Fehler bei Doji-Filter: {str(e)}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print("   ❌ Kein 'doji' in Technical Indicators gefunden")
                    else:
                        print("   ❌ Keine 'technical_indicators' in Patterns gefunden")
                    
                except Exception as e:
                    print(f"   ❌ Fehler bei Pattern-Erkennung: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ❌ Keine Daten von {exchange_name} für {symbol}")
        except Exception as e:
            print(f"   ❌ Fehler bei {exchange_name}: {str(e)}")
    
    # Auto-Exchange Modus testen
    print(f"\n6. OHLCV-Daten für {symbol} ({timeframe}) mit Auto-Exchange testen...")
    try:
        df = market_engine.get_ohlcv(symbol, timeframe, limit=limit)
        
        if df is not None and len(df) > 0:
            print(f"   ✅ Daten mit Auto-Exchange geladen: {len(df)} Datenpunkte")
            print(f"   Erste 3 Datenpunkte:")
            print(df.head(3))
            
            # Pattern-Test mit Auto-Exchange-Daten
            print(f"\n   Pattern-Erkennung für Auto-Exchange-Daten...")
            patterns = market_engine.detect_patterns(df)
            print(f"   Pattern-Typ: {type(patterns)}")
            print(f"   Pattern-Keys: {list(patterns.keys())}")
            
            # Auto-Exchange Doji-Filter testen
            try:
                print(f"\n   Doji-Filter mit Auto-Exchange-Daten testen...")
                filtered = market_engine.filter_patterns(
                    patterns, 
                    min_strength=0.0, 
                    pattern_types=['doji']
                )
                
                print(f"   Filter-Ergebnis: {type(filtered)}")
                print(f"   Filter-Keys: {list(filtered.keys()) if isinstance(filtered, dict) else 'NOT DICT'}")
            except Exception as e:
                print(f"   ❌ Fehler bei Doji-Filter (Auto): {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ❌ Keine Daten mit Auto-Exchange für {symbol}")
    except Exception as e:
        print(f"   ❌ Fehler bei Auto-Exchange: {str(e)}")
    
    return None

if __name__ == "__main__":
    try:
        test_ohlcv_with_wait()
        print("\n✅ Test abgeschlossen")
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {str(e)}")
        import traceback
        traceback.print_exc()
