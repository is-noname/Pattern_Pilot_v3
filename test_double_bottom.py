# test_double_bottom_render.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analysis_pipeline import analysis_pipeline
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def test_double_bottom_rendering():
    """
    Direkter Test des Double Bottom Pattern Renderings ohne Dashboard-Filter
    """
    print("🧪 Starting Double Bottom Render Test...")
    
    # 1. Daten laden
    result = analysis_pipeline.analyze_symbol("BTC/USDT", "1d", 200)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    df = result['data']
    patterns_dict = result['patterns']
    
    # 2. Direkt Double Bottom Pattern extrahieren
    if 'formation_patterns' in patterns_dict:
        double_bottom_patterns = patterns_dict['formation_patterns'].get('double_bottom', [])
    else:
        double_bottom_patterns = patterns_dict.get('double_bottom', [])
    
    print(f"🔍 Found {len(double_bottom_patterns)} double_bottom patterns")
    
    if not double_bottom_patterns:
        print("❌ No double_bottom patterns found to test")
        return
    
    # 3. Chart erstellen
    fig = make_subplots(rows=1, cols=1, subplot_titles=("Double Bottom Test",))
    
    # Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="BTC/USDT"
    ))
    
    # 4. DIRECT Pattern Rendering (bypass dispatcher)
    try:
        from core.patterns.formation_patterns.double_patterns import render_pattern_plotly
        
        for i, pattern in enumerate(double_bottom_patterns):
            print(f"🎨 Rendering pattern {i+1}: {pattern}")
            
            # Ensure pattern has type field
            if 'type' not in pattern:
                pattern['type'] = 'double_bottom'
            
            # Direct render call
            render_pattern_plotly(fig, df, pattern)
            
        print(f"✅ Rendered {len(double_bottom_patterns)} double_bottom overlays")
        
    except Exception as e:
        print(f"❌ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Chart konfigurieren
    fig.update_layout(
        title="Double Bottom Pattern Render Test",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        height=800
    )
    
    # 6. Chart anzeigen
    fig.show()
    print("🎯 Chart should open in browser - check for necklines and overlays!")

if __name__ == "__main__":
    test_double_bottom_rendering()
