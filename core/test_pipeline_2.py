import time
from core.market_engine import market_engine

print("⏳ Waiting for exchanges to load...")

# Wait until at least one exchange is online
max_wait = 30
waited = 0

while waited < max_wait:
    online_exchanges = []
    for name, ex in market_engine.exchanges.items():
        if not isinstance(ex, dict):  # Exchange object = online
            online_exchanges.append(name)

    if online_exchanges:
        print(f"✅ Exchanges online: {online_exchanges}")
        break

    print(f"⏳ Still loading... ({waited}s)")
    time.sleep(2)
    waited += 2

# Now test the pipeline
from core.analysis_pipeline import analysis_pipeline

from core.analysis_pipeline import analysis_pipeline

result = analysis_pipeline.analyze_symbol("BTC/USDT", "1d", 100)

# Check combined patterns
patterns = result.get('patterns', {})
print("✅ Pattern categories:", list(patterns.keys()))

# Count total patterns
total_count = analysis_pipeline.get_pattern_count("BTC/USDT", "1d")
print(f"✅ Total patterns: {total_count}")

result = analysis_pipeline.analyze_symbol("BTC/USDT", "1d", 100)