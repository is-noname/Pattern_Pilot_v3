# structure_test.py
# Test zum Aufdecken der Strukturkonflikte in der Pattern-Erkennung

import json
import inspect
from core.market_engine import MarketEngine
from core.analysis_pipeline import analysis_pipeline

def test_pattern_structures():
    """
    Test zum Aufdecken der Strukturkonflikte zwischen 
    verschiedenen Teilen der Anwendung.
    """
    print("🔍 Pattern-Struktur-Konflikt-Test")
    
    # MarketEngine initialisieren
    print("\n1. MarketEngine laden...")
    market_engine = MarketEngine()
    
    # Warten um sicherzustellen, dass die Exchanges geladen sind
    wait_for_exchanges(market_engine, max_wait=10)
    
    # Symbol und Timeframe
    symbol = "BTC/USDT"
    timeframe = "1d"
    limit = 100
    
    # OHLCV-Daten holen
    print(f"\n2. OHLCV-Daten für {symbol} ({timeframe}) laden...")
    df = market_engine.get_ohlcv(symbol, timeframe, limit=limit, exchange="binance")
    
    if df is None or len(df) == 0:
        print("   ❌ Keine Daten gefunden - Test kann nicht fortgesetzt werden")
        return
    
    print(f"   ✅ Daten geladen: {len(df)} Datenpunkte")
    
    # Test 1: Direkte Pattern-Erkennung mit market_engine
    print("\n3. Test 1: Direkte Pattern-Erkennung mit market_engine.detect_patterns...")
    patterns_market_engine = market_engine.detect_patterns(df)
    analyze_pattern_structure(patterns_market_engine, "market_engine.detect_patterns")
    
    # Test 2: Pattern-Erkennung über Analysis Pipeline
    print("\n4. Test 2: Pattern-Erkennung über analysis_pipeline.analyze_symbol...")
    result_pipeline = analysis_pipeline.analyze_symbol(symbol, timeframe)
    
    if not result_pipeline:
        print("   ❌ Keine Ergebnisse von analysis_pipeline")
    else:
        print(f"   ✅ Ergebnisse erhalten: {type(result_pipeline)}")
        if 'patterns' in result_pipeline:
            patterns_pipeline = result_pipeline['patterns']
            analyze_pattern_structure(patterns_pipeline, "analysis_pipeline.analyze_symbol['patterns']")
        else:
            print("   ❌ Keine 'patterns' in analysis_pipeline Ergebnissen")
    
    # Test 3: Zugriff auf Pattern Manager
    print("\n5. Test 3: Zugriff auf pattern_manager über analysis_pipeline...")
    try:
        pattern_manager = analysis_pipeline.pattern_manager
        print(f"   ✅ pattern_manager erhalten: {type(pattern_manager)}")
        
        # Pattern-Manager-Code untersuchen
        try:
            pm_source = inspect.getsource(pattern_manager.detect_patterns)
            print("   ✅ pattern_manager.detect_patterns Quellcode gefunden")
            print("   Erste 5 Zeilen:")
            for i, line in enumerate(pm_source.split('\n')[:5]):
                print(f"   {i+1}: {line}")
        except Exception as e:
            print(f"   ❌ Fehler beim Quellcode-Abruf: {str(e)}")
        
        # Pattern-Manager direkt aufrufen
        try:
            print("\n   Pattern-Manager direkt aufrufen...")
            pm_patterns = pattern_manager.detect_patterns(df, timeframe)
            analyze_pattern_structure(pm_patterns, "pattern_manager.detect_patterns")
        except Exception as e:
            print(f"   ❌ Fehler bei pattern_manager.detect_patterns: {str(e)}")
    except Exception as e:
        print(f"   ❌ Fehler beim Zugriff auf pattern_manager: {str(e)}")
    
    # Test 4: Filter-Methode untersuchen
    print("\n6. Test 4: filter_patterns Methode untersuchen...")
    try:
        filter_source = inspect.getsource(market_engine.filter_patterns)
        print("   ✅ market_engine.filter_patterns Quellcode gefunden")
        print("   Erste 10 Zeilen:")
        for i, line in enumerate(filter_source.split('\n')[:10]):
            print(f"   {i+1}: {line}")
    except Exception as e:
        print(f"   ❌ Fehler beim Quellcode-Abruf: {str(e)}")
    
    # Test 5: Filter für Doji mit market_engine Patterns
    print("\n7. Test 5: Filter für Doji mit market_engine Patterns...")
    try:
        doji_filtered = market_engine.filter_patterns(
            patterns_market_engine, 
            min_strength=0.0, 
            pattern_types=['doji']
        )
        analyze_pattern_structure(doji_filtered, "Doji-Filter-Ergebnis (market_engine)")
    except Exception as e:
        print(f"   ❌ Fehler bei Doji-Filter (market_engine): {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Filter für Doji mit analysis_pipeline Patterns (falls vorhanden)
    if 'patterns' in result_pipeline:
        print("\n8. Test 6: Filter für Doji mit analysis_pipeline Patterns...")
        try:
            doji_filtered_pipeline = market_engine.filter_patterns(
                result_pipeline['patterns'], 
                min_strength=0.0, 
                pattern_types=['doji']
            )
            analyze_pattern_structure(doji_filtered_pipeline, "Doji-Filter-Ergebnis (pipeline)")
        except Exception as e:
            print(f"   ❌ Fehler bei Doji-Filter (pipeline): {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Test 7: Filter für double_bottom mit market_engine Patterns
    print("\n9. Test 7: Filter für double_bottom mit market_engine Patterns...")
    try:
        double_filtered = market_engine.filter_patterns(
            patterns_market_engine, 
            min_strength=0.0, 
            pattern_types=['double_bottom']
        )
        analyze_pattern_structure(double_filtered, "Double-Bottom-Filter-Ergebnis (market_engine)")
    except Exception as e:
        print(f"   ❌ Fehler bei Double-Bottom-Filter (market_engine): {str(e)}")
    
    # Quellcode von app.py Pattern-Callback untersuchen
    print("\n10. Quellcode von app.py Pattern-Callback untersuchen...")
    try:
        import os
        if os.path.exists("app.py"):
            with open("app.py", "r") as f:
                app_content = f.read()
            
            # Nach relevanten Code-Abschnitten suchen
            pattern_callbacks = []
            lines = app_content.split('\n')
            for i, line in enumerate(lines):
                if "detect_patterns" in line or "filter_patterns" in line:
                    start = max(0, i-5)
                    end = min(len(lines), i+5)
                    pattern_callbacks.append("\n".join(lines[start:end]))
            
            if pattern_callbacks:
                print(f"   ✅ {len(pattern_callbacks)} relevante Code-Abschnitte in app.py gefunden")
                for i, code in enumerate(pattern_callbacks[:2]):  # Erste 2 Abschnitte anzeigen
                    print(f"\n   Abschnitt {i+1}:")
                    print("   " + "\n   ".join(code.split('\n')))
            else:
                print("   ❌ Keine relevanten Code-Abschnitte in app.py gefunden")
        else:
            print("   ❌ app.py nicht gefunden")
    except Exception as e:
        print(f"   ❌ Fehler beim Lesen von app.py: {str(e)}")

def wait_for_exchanges(market_engine, max_wait=10):
    """Wartet auf die Initialisierung der Exchanges"""
    import time
    
    print(f"   Warte bis zu {max_wait} Sekunden auf Exchange-Initialisierung...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        online_exchanges = []
        
        for name, exchange in market_engine.exchanges.items():
            if isinstance(exchange, object) and not isinstance(exchange, dict):
                online_exchanges.append(name)
        
        if len(online_exchanges) > 0:
            print(f"   ✅ {len(online_exchanges)} Exchanges online: {online_exchanges}")
            return
        
        time.sleep(1)
    
    print("   ⚠️ Zeitlimit erreicht, fahre trotzdem fort")

def analyze_pattern_structure(patterns, source_name):
    """Analysiert die Struktur eines Pattern-Dictionaries"""
    if patterns is None:
        print(f"   ❌ {source_name} lieferte None")
        return
    
    if not isinstance(patterns, dict):
        print(f"   ❌ {source_name} lieferte kein Dictionary, sondern {type(patterns)}")
        return
    
    print(f"   ✅ {source_name} lieferte ein Dictionary mit {len(patterns)} Top-Level-Keys")
    
    # Top-Level-Struktur
    print(f"   Top-Level-Keys: {list(patterns.keys())}")
    
    # Prüfen auf bekannte Strukturen
    has_technical = 'technical_indicators' in patterns
    has_formation = 'formation_patterns' in patterns
    
    if has_technical or has_formation:
        print(f"   🔍 VERSCHACHTELTE STRUKTUR erkannt")
        
        if has_technical:
            tech_indicators = patterns['technical_indicators']
            if isinstance(tech_indicators, dict):
                print(f"   technical_indicators: {len(tech_indicators)} Pattern-Typen")
                print(f"   Pattern-Typen: {list(tech_indicators.keys())}")
                
                # Doji speziell prüfen
                if 'doji' in tech_indicators:
                    doji = tech_indicators['doji']
                    print(f"   Doji: Typ = {type(doji)}, {len(doji) if isinstance(doji, list) else 'NOT LIST'}")
                    if isinstance(doji, list) and len(doji) > 0:
                        print(f"   Erstes Doji-Element: Typ = {type(doji[0])}")
                        if isinstance(doji[0], dict):
                            print(f"   Keys: {list(doji[0].keys())}")
                else:
                    print("   ❌ Kein 'doji' in technical_indicators")
            else:
                print(f"   ❌ technical_indicators ist kein Dictionary, sondern {type(tech_indicators)}")
        
        if has_formation:
            formations = patterns['formation_patterns']
            if isinstance(formations, dict):
                print(f"   formation_patterns: {len(formations)} Pattern-Typen")
                print(f"   Pattern-Typen: {list(formations.keys())}")
                
                # Double Bottom speziell prüfen
                if 'double_bottom' in formations:
                    double = formations['double_bottom']
                    print(f"   Double Bottom: Typ = {type(double)}, {len(double) if isinstance(double, list) else 'NOT LIST'}")
                    if isinstance(double, list) and len(double) > 0:
                        print(f"   Erstes Double-Bottom-Element: Typ = {type(double[0])}")
                        if isinstance(double[0], dict):
                            print(f"   Keys: {list(double[0].keys())}")
                else:
                    print("   ❌ Kein 'double_bottom' in formation_patterns")
            else:
                print(f"   ❌ formation_patterns ist kein Dictionary, sondern {type(formations)}")
    else:
        print(f"   🔍 FLACHE STRUKTUR erkannt")
        
        # Doji in flacher Struktur prüfen
        if 'doji' in patterns:
            doji = patterns['doji']
            print(f"   Doji: Typ = {type(doji)}, {len(doji) if isinstance(doji, list) else 'NOT LIST'}")
            if isinstance(doji, list) and len(doji) > 0:
                print(f"   Erstes Doji-Element: Typ = {type(doji[0])}")
                if isinstance(doji[0], dict):
                    print(f"   Keys: {list(doji[0].keys())}")
        else:
            print("   ❌ Kein 'doji' in flacher Struktur")
        
        # Double Bottom in flacher Struktur prüfen
        if 'double_bottom' in patterns:
            double = patterns['double_bottom']
            print(f"   Double Bottom: Typ = {type(double)}, {len(double) if isinstance(double, list) else 'NOT LIST'}")
            if isinstance(double, list) and len(double) > 0:
                print(f"   Erstes Double-Bottom-Element: Typ = {type(double[0])}")
                if isinstance(double[0], dict):
                    print(f"   Keys: {list(double[0].keys())}")
        else:
            print("   ❌ Kein 'double_bottom' in flacher Struktur")
    
    # Einen zufälligen Pattern-Typ untersuchen
    if len(patterns) > 0:
        sample_key = list(patterns.keys())[0]
        sample_value = patterns[sample_key]
        
        print(f"   Beispiel: {sample_key}")
        print(f"   Typ: {type(sample_value)}")
        
        if isinstance(sample_value, list):
            print(f"   Länge: {len(sample_value)}")
            if len(sample_value) > 0:
                print(f"   Erstes Element: Typ = {type(sample_value[0])}")
                if isinstance(sample_value[0], dict):
                    print(f"   Keys: {list(sample_value[0].keys())}")
        elif isinstance(sample_value, dict):
            print(f"   Keys: {list(sample_value.keys())}")

if __name__ == "__main__":
    try:
        test_pattern_structures()
        print("\n✅ Test abgeschlossen")
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {str(e)}")
        import traceback
        traceback.print_exc()
