# test_pipeline.py
try:
    from core.analysis_pipeline import analysis_pipeline

    print(f"✅ Pipeline imported: {type(analysis_pipeline)}")

    # Singleton Test
    from core.analysis_pipeline import AnalysisPipeline

    pipeline2 = AnalysisPipeline()
    print(f"✅ Singleton verified: {pipeline2 is analysis_pipeline}")

    # Single Symbol Test
    result = analysis_pipeline.analyze_symbol("BTC/USDT", "1d", 100)
    print(f"Patterns found: {analysis_pipeline.get_pattern_count('BTC/USDT', '1d')}")

    from core.analysis_pipeline import analysis_pipeline
    result = analysis_pipeline.analyze_symbol("BTC/USDT", "1d", 100)

except Exception as e:
    print(f"❌ Import failed: {e}")