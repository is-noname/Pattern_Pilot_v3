# test_pattern_analyzer.py
import pandas as pd
from cache.cache_manager import cache_instance
from patterns import detect_all_patterns
from analyze.pattern_analyzer import PatternAnalyzer  # Klasse importieren statt Singleton
from api.api_manager import APIManager


def test_pattern_analyzer():
    """Test für den PatternAnalyzer mit BTC-Daten aus dem Cache"""
    print("🧪 Starting PatternAnalyzer Test")

    # 1. Cache initialisieren und BTC-Daten prüfen
    cache = cache_instance
    btc_data = cache.get_cached_data("BTC", timeframe="1d")

    # Falls keine Daten im Cache, lade sie über API
    if btc_data is None or btc_data.empty:
        print("⚠️ Keine BTC-Daten im Cache gefunden, lade über API...")
        api_manager = APIManager()
        result = api_manager.get_ohlcv("BTC", timeframe="1d", days=180)

        # In Cache speichern
        if not result['data'].empty:
            cache.save_asset_data("BTC", result)
            print(f"✅ {len(result['data'])} BTC-Datenpunkte in Cache gespeichert")
            btc_data = result['data']
        else:
            print("❌ Konnte keine BTC-Daten laden!")
            return
    else:
        print(f"✅ BTC-Daten aus Cache geladen: {len(btc_data)} Datenpunkte")

    # 2. Patterns erkennen
    patterns = detect_all_patterns(btc_data, timeframe="1d")

    pattern_count = sum(len(p) for p in patterns.values())
    print(f"✅ {pattern_count} Patterns gefunden")

    # 3. Einfachen Analyse-State erstellen
    class SimpleState:
        def __init__(self):
            self.timeframe_patterns = {"1d": patterns}

    state = SimpleState()

    # 4. Eigenen PatternAnalyzer mit unserem State initialisieren
    analyzer = PatternAnalyzer(state)

    # 5. Patterns analysieren
    analyzed_patterns = analyzer.analyze_patterns(patterns, btc_data, "1d")

    # 6. Stärkste Patterns ausgeben
    strongest_patterns = analyzer.get_strongest_patterns(analyzed_patterns, min_strength=0.5)

    print(f"\n🔍 Top {len(strongest_patterns)} Patterns:")
    for idx, pattern in enumerate(strongest_patterns, 1):
        pattern_data = pattern['data']
        pattern_type = pattern['type'].replace('_', ' ').title()
        strength = pattern_data.get('strength', 0)
        direction = pattern_data.get('direction', 'unknown')
        confirmed = "✓" if pattern_data.get('confirmed', False) else "✗"

        print(f"{idx}. {pattern_type} ({direction}) - Stärke: {strength:.2f} - Bestätigt: {confirmed}")

        # Kursziel und Stop-Loss, falls vorhanden
        if pattern_data.get('target') is not None:
            current = btc_data['close'].iloc[-1]
            target = pattern_data.get('target')
            target_pct = ((target - current) / current) * 100
            print(f"   Target: ${target:.2f} ({target_pct:+.2f}%)")

        if pattern_data.get('stop_loss') is not None:
            stop = pattern_data.get('stop_loss')
            stop_pct = ((stop - current) / current) * 100
            print(f"   Stop-Loss: ${stop:.2f} ({stop_pct:+.2f}%)")

        # Risk-Reward Ratio
        if pattern_data.get('risk_reward_ratio') is not None:
            print(f"   Risk-Reward: {pattern_data['risk_reward_ratio']:.2f}")

        print()

        print("\n📋 Vollständige Details eines Patterns:")
        if strongest_patterns:
            pattern = strongest_patterns[0]  # Erstes Pattern
            print(f"Pattern-Typ: {pattern['type']}")
            for key, value in pattern['data'].items():
                print(f"  {key}: {value}")

        print("\n🎯 Support/Resistance-Levels:")
        # Bereite Daten für mehrere Timeframes vor (falls vorhanden)
        timeframe_data = {"1d": btc_data}
        timeframe_patterns = {"1d": patterns}

        # Support/Resistance-Levels extrahieren
        key_levels = analyzer.extract_key_levels(timeframe_data, timeframe_patterns)

        # Zeige Top-Levels
        print("Support-Levels:")
        for level in key_levels.get('support', [])[:3]:  # Top 3
            print(f"  ${level['price']:.2f} (Stärke: {level.get('importance', 0):.2f})")

        print("Resistance-Levels:")
        for level in key_levels.get('resistance', [])[:3]:  # Top 3
            print(f"  ${level['price']:.2f} (Stärke: {level.get('importance', 0):.2f})")

        # Mehrere Timeframes laden und Konflikte analysieren
        timeframes = ["1d", "1w"]  # Beispiel mit zwei Timeframes
        timeframe_data = {}
        timeframe_patterns = {}

        for tf in timeframes:
            tf_data = cache.get_cached_data("BTC", timeframe=tf)
            if tf_data is not None and not tf_data.empty:
                timeframe_data[tf] = tf_data
                timeframe_patterns[tf] = detect_all_patterns(tf_data, timeframe=tf)

        # Konflikte analysieren, falls mehrere Timeframes vorhanden
        if len(timeframe_data) > 1:
            print("\n⚠️ Timeframe-Konflikte:")
            conflicts = analyzer.analyze_timeframe_conflicts(timeframe_data, timeframe_patterns)

            for idx, conflict in enumerate(conflicts, 1):
                print(f"{idx}. {conflict.get('description', 'Unbekannter Konflikt')}")
                print(f"   Schweregrad: {conflict.get('severity', 'unknown')}")
                print(f"   Timeframes: {', '.join(conflict.get('timeframes', []))}")
                print(f"   Empfehlung: {conflict.get('recommendation', '')}")
                print()

        # Risiko-Ertrags-Analyse über alle Patterns
        print("\n📊 Risiko-Ertrags-Analyse:")
        rr_ratios = []

        for pattern_type, patterns_list in analyzed_patterns.items():
            for pattern in patterns_list:
                if pattern.get('risk_reward_ratio') is not None:
                    rr_ratios.append({
                        'type': pattern_type,
                        'ratio': pattern['risk_reward_ratio'],
                        'confirmed': pattern.get('confirmed', False)
                    })

        if rr_ratios:
            avg_ratio = sum(item['ratio'] for item in rr_ratios) / len(rr_ratios)
            best_ratio = max(rr_ratios, key=lambda x: x['ratio'])

            print(f"Durchschnitt: {avg_ratio:.2f}")
            print(f"Bestes Verhältnis: {best_ratio['ratio']:.2f} ({best_ratio['type']})")

            # Bestätigte vs. unbestätigte Patterns
            confirmed = [item for item in rr_ratios if item['confirmed']]
            if confirmed:
                avg_confirmed = sum(item['ratio'] for item in confirmed) / len(confirmed)
                print(f"Durchschnitt bestätigte Patterns: {avg_confirmed:.2f}")

        # Pattern-Verteilung nach Kategorien
        from core.patterns.chart_patterns.pattern_categories import ALL_BULLISH, ALL_BEARISH, ALL_NEUTRAL

        print("\n📊 Pattern-Verteilung:")
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for pattern_type, patterns_list in patterns.items():
            count = len(patterns_list)
            if pattern_type in ALL_BULLISH:
                bullish_count += count
            elif pattern_type in ALL_BEARISH:
                bearish_count += count
            else:
                neutral_count += count

        total = bullish_count + bearish_count + neutral_count
        if total > 0:
            print(f"Bullish: {bullish_count} ({bullish_count / total * 100:.1f}%)")
            print(f"Bearish: {bearish_count} ({bearish_count / total * 100:.1f}%)")
            print(f"Neutral: {neutral_count} ({neutral_count / total * 100:.1f}%)")

        # Pattern-Stärke detailliert analysieren
        print("\n🔍 Detaillierte Pattern-Stärke-Analyse:")
        if strongest_patterns:
            pattern = strongest_patterns[0]  # Stärkstes Pattern
            pattern_data = pattern['data']

            # Faktoren für Stärkeberechnung anzeigen
            factors = {
                "confirmation": 0.3,  # Bestätigung des Musters
                "timeframe_level": 0.2,  # Höhere Timeframes haben mehr Gewicht
                "pattern_quality": 0.2,  # Qualität des Musters (Größe, Symmetrie, etc.)
                "higher_tf_alignment": 0.2,  # Übereinstimmung mit höheren Timeframes
                "volume_conf": 0.1,  # Volumenbestätigung
            }

            print(f"Pattern: {pattern['type'].replace('_', ' ').title()}")
            print(f"Gesamtstärke: {pattern_data.get('strength', 0):.2f}")
            print("Stärke-Faktoren:")

            # Bestätigung
            factor_value = factors["confirmation"] if pattern_data.get('confirmed', False) else 0
            print(f"  Bestätigung: {factor_value:.2f} (max {factors['confirmation']:.2f})")

            # Timeframe-Level (1d = 0.6)
            print(f"  Timeframe-Level: {0.6 * factors['timeframe_level']:.2f} (max {factors['timeframe_level']:.2f})")

            # Pattern-Qualität könnte man aus den Daten ableiten
            if 'symmetry' in pattern_data:
                print(f"  Pattern-Qualität/Symmetrie: {pattern_data['symmetry']:.2f}")

        # Zeige Timeframe-Gewichtung für Support/Resistance
        print("\n⚖️ Timeframe-Gewichtung:")
        print("  1d: 1.0x")
        print("  3d: 1.5x")
        print("  1w: 2.0x")
        print("  1m: 3.0x")

        # Zeige die Stärke aller gefundenen Patterns
        print("\n📊 Stärke aller Patterns:")
        all_patterns = []

        for pattern_type, patterns_list in analyzed_patterns.items():
            for pattern in patterns_list:
                all_patterns.append({
                    'type': pattern_type,
                    'strength': pattern.get('strength', 0),
                    'confirmed': pattern.get('confirmed', False)
                })

        # Nach Stärke sortieren
        all_patterns.sort(key=lambda x: x['strength'], reverse=True)

        # Als Tabelle ausgeben
        print(f"{'Pattern-Typ':<25} {'Stärke':<10} {'Bestätigt'}")
        print("-" * 45)
        for p in all_patterns:
            pattern_name = p['type'].replace('_', ' ').title()
            confirmed = "✓" if p['confirmed'] else "✗"
            print(f"{pattern_name:<25} {p['strength']:<10.2f} {confirmed}")

        # Trading-Empfehlung testen
        print("\n💹 Trading-Empfehlung:")
        if btc_data is not None and not btc_data.empty:
            current_price = btc_data['close'].iloc[-1]
            recommendation = analyzer.generate_trading_recommendation(
                analyzed_patterns,
                current_price,
                timeframe="1d"
            )

            # Ausgabe formatieren
            action_emojis = {
                "BUY": "🟢",
                "SELL": "🔴",
                "NEUTRAL": "⚪"
            }

            emoji = action_emojis.get(recommendation["action"], "⚪")
            print(f"{emoji} Empfehlung: {recommendation['action']}")
            print(f"Konfidenz: {recommendation['confidence']:.2f}")
            print(f"Grund: {recommendation['reason']}")
            print(f"Risiko: {recommendation['risk_level']}")
            print(f"Basierend auf: {recommendation['based_on_pattern']}")

            if "target" in recommendation:
                print(f"Kursziel: ${recommendation['target']:.2f} ({recommendation['target_percent']:+.2f}%)")

            if "stop_loss" in recommendation:
                print(f"Stop-Loss: ${recommendation['stop_loss']:.2f} ({recommendation['stop_loss_percent']:+.2f}%)")


if __name__ == "__main__":
    test_pattern_analyzer()

