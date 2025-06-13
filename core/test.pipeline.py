# test_pipeline.py
try:
    from core.analysis_pipeline import analysis_pipeline

    print(f"✅ Pipeline imported: {type(analysis_pipeline)}")

    # Singleton Test
    from core.analysis_pipeline import AnalysisPipeline

    pipeline2 = AnalysisPipeline()
    print(f"✅ Singleton verified: {pipeline2 is analysis_pipeline}")

    # Debug Test - add this to your test:
    from core.market_engine import market_engine

    # 1. Check exchange status
    print("Exchange Status:")
    for name, ex in market_engine.exchanges.items():
        if isinstance(ex, dict):
            print(f"  {name}: {ex}")
        else:
            print(f"  {name}: ONLINE (has {len(ex.markets)} markets)")

    # 2. Debug get_ohlcv step by step
    print("\n🔍 Debug OHLCV fetch:")

    # Check if exchange_order gets populated
    df = market_engine.get_ohlcv("BTC/USDT", "1d", 100)





except Exception as e:
    print(f"❌ Import failed: {e}")