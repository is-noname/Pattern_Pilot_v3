# app.py - Pattern Pilot v2 Main App
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.market_engine import market_engine

# Page config
st.set_page_config(
    page_title="Pattern Pilot v2",
    page_icon="🚀", 
    layout="wide"
)

# Custom CSS für Dark Theme
st.markdown("""
<style>
.main { background-color: #0e1117; }
.stSelectbox > div > div { background-color: #262730; }
.stTextInput > div > div { background-color: #262730; }
</style>
""", unsafe_allow_html=True)

def main():
    """Main app function - Mega-simpel dank MarketEngine"""
    
    # 🎯 Header - Eine Zeile statt create_header() Funktion
    st.title("🚀 Pattern Pilot v2 - Profi Edition")
    
    # 📊 Input Controls - Viel simpler als v1
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        # Auto-complete für Symbols (dank ccxt)
        available_symbols = market_engine.get_available_symbols()[:50]  # Top 50
        symbol = st.selectbox(
            "Trading Pair", 
            available_symbols,
            index=0 if 'BTC/USDT' not in available_symbols else available_symbols.index('BTC/USDT')
        )
    
    with col2:
        timeframe = st.selectbox(
            "Timeframe",
            ['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
            index=5  # Default 1d
        )
    
    with col3:
        limit = st.number_input("Candles", min_value=50, max_value=1000, value=200)
    
    with col4:
        exchange = st.selectbox(
            "Exchange", 
            ['auto'] + list(market_engine.exchanges.keys()),
            index=0
        )
    
    # 🔍 Analysis Button
    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        analyze_symbol(symbol, timeframe, limit, exchange)
    
    # 💡 Quick Info Sidebar
    with st.sidebar:
        st.markdown("## 🚀 Pattern Pilot v2")
        st.markdown("**Powered by:**")
        st.markdown("- 🔥 ccxt (130+ exchanges)")
        st.markdown("- 📊 talib (150+ patterns)")
        st.markdown("- 📈 plotly (interactive charts)")
        
        # Exchange Status
        st.markdown("### 📡 Exchange Status")
        exchange_info = market_engine.get_exchange_info()
        for name, info in exchange_info.items():
            status = "🟢" if info.get('status') == 'online' else "🔴"
            markets = info.get('markets', 0)
            st.text(f"{status} {name}: {markets} markets")


def analyze_symbol(symbol: str, timeframe: str, limit: int, exchange: str):
    """Analyze symbol - Eine Funktion statt ganzes Modul"""
    
    with st.spinner(f"🔄 Loading {symbol} data..."):
        
        # 📊 Get Data (eine Zeile statt API-Manager-Chaos)
        ex = None if exchange == 'auto' else exchange
        df = market_engine.get_ohlcv(symbol, timeframe, limit, ex)
        
        if df.empty:
            st.error(f"❌ No data found for {symbol}")
            return
        
        st.success(f"✅ Loaded {len(df)} candles from {exchange}")
    
    # 🎯 Pattern Detection (eine Zeile statt patterns/__init__.py)
    with st.spinner("🎯 Detecting patterns..."):
        patterns = market_engine.detect_patterns(df)
        
        pattern_count = sum(len(signals) for signals in patterns.values())
        st.info(f"🎯 Found {pattern_count} pattern signals in {len(patterns)} categories")
    
    # 📈 Interactive Chart (plotly statt matplotlib)
    create_interactive_chart(df, patterns, symbol, timeframe)
    
    # 📋 Pattern Summary Table
    display_pattern_summary(patterns)


def create_interactive_chart(df: pd.DataFrame, patterns: dict, symbol: str, timeframe: str):
    """Interactive plotly chart - besser als matplotlib"""
    
    # Create subplots: Candlestick + Volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{symbol} ({timeframe})', 'Volume'),
        row_width=[0.7, 0.3]
    )
    
    # 🕯️ Candlestick Chart
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'], 
            low=df['low'],
            close=df['close'],
            name="Price",
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ),
        row=1, col=1
    )
    
    # 📊 Volume Bars  
    colors = ['#00ff88' if close >= open else '#ff4444' 
             for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df['datetime'],
            y=df['volume'],
            name="Volume",
            marker_color=colors,
            opacity=0.6
        ),
        row=2, col=1
    )
    
    # 🎯 Pattern Overlays - Automatisch für alle gefundenen Pattern
    pattern_colors = {
        'bullish': '#00ff88',
        'bearish': '#ff4444', 
        'neutral': '#ffaa00'
    }
    
    for pattern_name, signals in patterns.items():
        if not signals:
            continue
            
        for signal in signals:
            direction = signal.get('direction', 'neutral')
            color = pattern_colors.get(direction, '#ffffff')
            
            # Pattern-Marker hinzufügen
            fig.add_trace(
                go.Scatter(
                    x=[signal['datetime']],
                    y=[signal['price']],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=15,
                        color=color,
                        line=dict(width=2, color='white')
                    ),
                    name=f"{pattern_name} ({direction})",
                    hovertemplate=f"<b>{pattern_name}</b><br>" +
                                f"Direction: {direction}<br>" +
                                f"Strength: {signal.get('strength', 0):.2f}<br>" +
                                f"Price: ${signal['price']:.4f}<extra></extra>",
                    showlegend=True
                ),
                row=1, col=1
            )
    
    # 🎨 Layout Styling - Dark theme wie v1
    fig.update_layout(
        height=800,
        template='plotly_dark',
        title=f"📊 {symbol} Technical Analysis",
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Chart anzeigen - Interaktiv!
    st.plotly_chart(fig, use_container_width=True)


def display_pattern_summary(patterns: dict):
    """Pattern Summary Table - Übersichtlicher als v1"""
    
    if not patterns:
        st.info("No patterns detected")
        return
    
    st.markdown("### 🎯 Pattern Summary")
    
    # Flatten patterns für Table
    pattern_rows = []
    for pattern_name, signals in patterns.items():
        for signal in signals:
            pattern_rows.append({
                'Pattern': pattern_name.replace('_', ' ').title(),
                'Direction': signal.get('direction', 'neutral'),
                'Strength': f"{signal.get('strength', 0):.2f}",
                'Price': f"${signal['price']:.4f}",
                'Time': signal['datetime'].strftime('%Y-%m-%d %H:%M'),
            })
    
    if pattern_rows:
        # Convert to DataFrame für schöne Anzeige
        summary_df = pd.DataFrame(pattern_rows)
        
        # Color-coding mit Streamlit
        def highlight_direction(val):
            color = {
                'bullish': 'color: #00ff88',
                'bearish': 'color: #ff4444', 
                'neutral': 'color: #ffaa00'
            }.get(val, '')
            return color
        
        styled_df = summary_df.style.applymap(
            highlight_direction, subset=['Direction']
        )
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Quick Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            bullish_count = len([r for r in pattern_rows if r['Direction'] == 'bullish'])
            st.metric("🟢 Bullish Signals", bullish_count)
        with col2:
            bearish_count = len([r for r in pattern_rows if r['Direction'] == 'bearish'])
            st.metric("🔴 Bearish Signals", bearish_count)
        with col3:
            avg_strength = sum(float(r['Strength']) for r in pattern_rows) / len(pattern_rows)
            st.metric("💪 Avg Strength", f"{avg_strength:.2f}")


if __name__ == "__main__":
    main()