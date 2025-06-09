# app_streamlit.py - Pattern Pilot v2 Main App
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from core.market_engine_async import market_engine

# Page config
st.set_page_config(
    page_title="Pattern Pilot v2",
    page_icon="🚀", 
    layout="wide"
)

# 🎨 Cyberpunk CSS - Pattern Pilot v3.1
st.markdown("""
<style>
/* Matrix/Cyberpunk Theme */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

.main { 
    background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
    font-family: 'Orbitron', monospace;
}

/* Neon glow effects */
.stSelectbox > div > div, .stTextInput > div > div { 
    background: rgba(13, 13, 43, 0.8);
    border: 1px solid #00ff88;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    border-radius: 8px;
}

/* Title glow */
h1 {
    color: #00ff88 !important;
    text-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
    font-family: 'Orbitron', monospace !important;
    font-weight: 900 !important;
    text-align: center;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { text-shadow: 0 0 20px rgba(0, 255, 136, 0.8); }
    50% { text-shadow: 0 0 30px rgba(0, 255, 136, 1), 0 0 40px rgba(0, 255, 136, 0.8); }
}

/* Button styling */
.stButton > button {
    background: linear-gradient(45deg, #ff0080, #00ff88);
    border: none;
    color: white;
    font-weight: bold;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(255, 0, 128, 0.4);
    transition: all 0.3s ease;
    font-family: 'Orbitron', monospace;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.6);
    background: linear-gradient(45deg, #00ff88, #ff0080);
}

/* Metrics cards */
.metric-card {
    background: rgba(13, 13, 43, 0.9);
    border: 1px solid #00ff88;
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem;
    box-shadow: 0 4px 20px rgba(0, 255, 136, 0.2);
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0, 255, 136, 0.4);
    border-color: #ff0080;
}

/* Exchange status indicators */
.exchange-online { color: #00ff88; text-shadow: 0 0 10px #00ff88; }
.exchange-offline { color: #ff4444; text-shadow: 0 0 10px #ff4444; }

/* Pattern strength bars */
.strength-bar {
    height: 8px;
    background: linear-gradient(90deg, #ff4444, #ffaa00, #00ff88);
    border-radius: 4px;
    margin: 5px 0;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

/* Sidebar styling */
.css-1d391kg { background: rgba(13, 13, 43, 0.95) !important; }
.css-1d391kg .css-17eq0hr { color: #00ff88 !important; }

/* Success/Error messages with glow */
.stSuccess { 
    background: rgba(0, 255, 136, 0.1) !important;
    border: 1px solid #00ff88 !important;
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
}

.stError { 
    background: rgba(255, 68, 68, 0.1) !important;
    border: 1px solid #ff4444 !important;
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(255, 68, 68, 0.3);
}

.stInfo { 
    background: rgba(255, 170, 0, 0.1) !important;
    border: 1px solid #ffaa00 !important;
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(255, 170, 0, 0.3);
}

/* Matrix rain effect (optional) */
.matrix-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0.1;
    z-index: -1;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main app function - Now with Cyberpunk Power! 🚀"""
    
    # 🎯 Header - Cyberpunk Edition
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>🚀 PATTERN PILOT v3.1</h1>
        <p style="color: #00ff88; font-family: 'Orbitron', monospace; font-size: 1.2rem;">
            ⚡ CYBERPUNK TRADING ANALYSIS ⚡
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 📊 Enhanced Input Controls with icons
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        # Auto-complete für Symbols (dank ccxt)
        available_symbols = market_engine.get_available_symbols()[:50]  # Top 50
        symbol = st.selectbox(
            "🎯 Trading Pair", 
            available_symbols,
            index=0 if 'BTC/USDT' not in available_symbols else available_symbols.index('BTC/USDT')
        )
    
    with col2:
        timeframe = st.selectbox(
            "⏰ Timeframe",
            ['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
            index=5  # Default 1d
        )
    
    with col3:
        limit = st.number_input("📈 Candles", min_value=50, max_value=1000, value=200)
    
    with col4:
        exchange = st.selectbox(
            "🏢 Exchange", 
            ['auto'] + list(market_engine.exchanges.keys()),
            index=0
        )
    
    # 🔍 Enhanced Analysis Button with glow
    if st.button("🔍 ANALYZE TARGET", type="primary", use_container_width=True):
        analyze_symbol(symbol, timeframe, limit, exchange)
    
    # 💡 Enhanced Sidebar with live stats
    with st.sidebar:
        st.markdown("""
        <div class="metric-card">
            <h2 style="color: #00ff88; text-align: center;">🚀 PILOT STATUS</h2>
            <p style="color: #00ff88; text-align: center;">Neural Networks Online</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ⚡ Power Source")
        st.markdown("- 🔥 **ccxt** (130+ exchanges)")
        st.markdown("- 📊 **Custom AI** (Pattern detection)")
        st.markdown("- 📈 **plotly** (Quantum charts)")
        
        # Live Exchange Status with glow effects
        st.markdown("### 📡 Exchange Matrix")
        exchange_info = market_engine.get_exchange_info()
        for name, info in exchange_info.items():
            if info.get('status') == 'online':
                markets = info.get('markets', 0)
                st.markdown(f"""
                <div style="color: #00ff88; text-shadow: 0 0 10px #00ff88;">
                    🟢 {name.upper()}: {markets:,} markets
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="color: #ff4444; text-shadow: 0 0 10px #ff4444;">
                    🔴 {name.upper()}: OFFLINE
                </div>
                """, unsafe_allow_html=True)


def analyze_symbol(symbol: str, timeframe: str, limit: int, exchange: str):
    """Enhanced Analysis with Cyberpunk feedback! ⚡"""
    
    # 🎯 Loading with style
    with st.spinner("🔄 Infiltrating market matrix..."):
        
        # 📊 Get Data with enhanced feedback
        ex = None if exchange == 'auto' else exchange
        df = market_engine.get_ohlcv(symbol, timeframe, limit, ex)
        
        if df.empty:
            st.error(f"❌ **SIGNAL LOST**: No data found for {symbol}")
            st.markdown("""
            <div style="color: #ff4444; text-align: center; font-family: 'Orbitron';">
                🛰️ Satellite link compromised. Try different exchange or symbol.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Enhanced success message
        st.success(f"✅ **DATA ACQUIRED**: {len(df):,} candles from {exchange.upper() if exchange != 'auto' else 'AUTO-ROUTE'}")
    
    # 🎯 Pattern Detection with cyber styling
    with st.spinner("🧠 Neural pattern analysis in progress..."):
        patterns = market_engine.detect_patterns(df)
        
        pattern_count = sum(len(signals) for signals in patterns.values())
        
        if pattern_count > 0:
            st.info(f"🎯 **PATTERNS DETECTED**: {pattern_count} signals across {len(patterns)} categories")
            
            # Pattern breakdown
            breakdown = []
            for pattern_name, signals in patterns.items():
                if signals:
                    breakdown.append(f"**{pattern_name.replace('_', ' ').title()}**: {len(signals)}")
            
            if breakdown:
                st.markdown("**🔍 Signal Breakdown:**")
                st.markdown(" • ".join(breakdown))
        else:
            st.warning("⚠️ **SCAN COMPLETE**: No significant patterns detected")
    
    # 📈 Enhanced Chart with cyber theme
    create_enhanced_chart(df, patterns, symbol, timeframe)
    
    # 📋 Enhanced Pattern Summary
    display_enhanced_pattern_summary(patterns, symbol)


def create_enhanced_chart(df: pd.DataFrame, patterns: dict, symbol: str, timeframe: str):
    """Enhanced Cyberpunk Chart with better pattern visualization! 🎯"""
    
    # Create subplots: Candlestick + Volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'⚡ {symbol} NEURAL ANALYSIS ({timeframe})', '🔊 VOLUME MATRIX'),
        row_width=[0.7, 0.3]
    )
    
    # 🕯️ Enhanced Candlestick Chart
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'], 
            low=df['low'],
            close=df['close'],
            name="Price Matrix",
            increasing_line_color='#06fc99',
            decreasing_line_color='#ff0080',
            increasing_fillcolor='rgba(0, 255, 136, 0.8)',
            decreasing_fillcolor='rgba(255, 0, 128, 0.8)'
        ),
        row=1, col=1
    )
    
    # 📊 Enhanced Volume Bars with neon colors
    colors = ['rgba(0, 255, 136, 0.8)' if close >= open else 'rgba(255, 0, 128, 0.8)' 
             for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df['datetime'],
            y=df['volume'],
            name="Volume Flow",
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )

    # 🎯 Enhanced Pattern Overlays with unique icons
    pattern_styles = {
        'doji': {'symbol': 'circle', 'color': '#ffaa00', 'size': 12, 'emoji': '🎯'},
        'hammer': {'symbol': 'triangle-up', 'color': '#00ff88', 'size': 15, 'emoji': '🔨'},
        'engulfing': {'symbol': 'star', 'color': '#ff0080', 'size': 18, 'emoji': '🌟'},
        'ma_crossover': {'symbol': 'diamond', 'color': '#00aaff', 'size': 14, 'emoji': '💎'},
        'support_resistance': {'symbol': 'square', 'color': '#aa00ff', 'size': 10, 'emoji': '🔷'},
        'hanging_man': {'symbol': 'triangle-down', 'color': '#ff4444', 'size': 15, 'emoji': '⚠️'},
        'shooting_star': {'symbol': 'star-triangle-up', 'color': '#ff6600', 'size': 16, 'emoji': '⭐'},
        'morning_star': {'symbol': 'star-square', 'color': '#66ff66', 'size': 17, 'emoji': '🌅'},
        'evening_star': {'symbol': 'star-diamond', 'color': '#ff3366', 'size': 17, 'emoji': '🌆'},
        'three_white_soldiers': {'symbol': 'arrow-up', 'color': '#44ff44', 'size': 20, 'emoji': '⬆️'},
        'three_black_crows': {'symbol': 'arrow-down', 'color': '#ff4444', 'size': 20, 'emoji': '⬇️'},
        'harami': {'symbol': 'hourglass', 'color': '#ffaa44', 'size': 13, 'emoji': '⏳'},
        'piercing': {'symbol': 'triangle-up-open', 'color': '#44aa44', 'size': 14, 'emoji': '🔺'},
        'dark_cloud': {'symbol': 'triangle-down-open', 'color': '#aa4444', 'size': 14, 'emoji': '🔻'},
    }
    
    pattern_legend_added = set()  # Track which patterns are in legend
    
    for pattern_name, signals in patterns.items():
        if not signals:
            continue
        
        style = pattern_styles.get(pattern_name, {
            'symbol': 'circle',
            'color': '#ffffff',
            'size': 12,
            'emoji': '📊'
        })
        
        for i, signal in enumerate(signals):
            direction = signal.get('direction', 'neutral')
            strength = signal.get('strength', 0.5)
            
            # Color adjustment based on direction
            if direction == 'bullish':
                color = '#00ff88'
            elif direction == 'bearish':
                color = '#ff0080'
            elif direction == 'resistance':
                color = '#ff4444'
            elif direction == 'support':
                color = '#00ff88'
            else:
                color = style['color']
            
            # Show legend only for first occurrence of each pattern
            show_legend = pattern_name not in pattern_legend_added
            if show_legend:
                pattern_legend_added.add(pattern_name)
            
            # Enhanced pattern marker
            fig.add_trace(
                go.Scatter(
                    x=[signal['datetime']],
                    y=[signal['price']],
                    mode='markers',
                    marker=dict(
                        symbol=style['symbol'],
                        size=style['size'] + (strength * 8),  # Size based on strength
                        color=color,
                        line=dict(width=3, color='white'),
                        opacity=0.8 + (strength * 0.2)
                    ),
                    name=f"{style['emoji']} {pattern_name.replace('_', ' ').title()}",
                    hovertemplate=f"<b>{style['emoji']} {pattern_name.replace('_', ' ').title()}</b><br>" +
                                f"🎯 Direction: {direction}<br>" +
                                f"💪 Strength: {strength:.2f}<br>" +
                                f"💰 Price: ${signal['price']:.4f}<br>" +
                                f"⏰ Time: %{{x}}<extra></extra>",
                    showlegend=show_legend,
                    legendgroup=pattern_name
                ),
                row=1, col=1
            )
    
    # 🎨 Cyberpunk Layout Styling
    fig.update_layout(
        height=900,
        template='plotly_dark',
        title=dict(
            text=f"🚀 {symbol} QUANTUM ANALYSIS",
            font=dict(family="Orbitron", size=20, color="#00ff88"),
            x=0.5
        ),
        paper_bgcolor='rgba(10, 14, 39, 0.9)',
        plot_bgcolor='rgba(13, 13, 43, 0.8)',
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(13, 13, 43, 0.8)",
            bordercolor="#00ff88",
            borderwidth=1,
            font=dict(family="Orbitron", color="#00ff88")
        ),
        # Grid styling
        xaxis=dict(
            gridcolor='rgba(0, 255, 136, 0.2)',
            gridwidth=1
        ),
        yaxis=dict(
            gridcolor='rgba(0, 255, 136, 0.2)',
            gridwidth=1
        ),
        xaxis2=dict(
            gridcolor='rgba(0, 255, 136, 0.2)',
            gridwidth=1
        ),
        yaxis2=dict(
            gridcolor='rgba(0, 255, 136, 0.2)',
            gridwidth=1
        )
    )
    
    # Chart anzeigen mit full width
    st.plotly_chart(fig, use_container_width=True)


def display_enhanced_pattern_summary(patterns: dict, symbol: str):
    """Enhanced Pattern Summary with Cyberpunk vibes! 🎯"""
    
    if not patterns:
        st.markdown("""
        <div style="text-align: center; color: #ffaa00; font-family: 'Orbitron'; margin: 2rem;">
            🔍 <b>NEURAL SCAN COMPLETE</b><br>
            No patterns detected in current timeframe.<br>
            Consider adjusting parameters or timeframe.
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("### 🎯 PATTERN INTELLIGENCE REPORT")
    
    # Create enhanced metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate pattern statistics
    all_signals = []
    for signals in patterns.values():
        all_signals.extend(signals)
    
    if all_signals:
        bullish_count = len([s for s in all_signals if s.get('direction') == 'bullish'])
        bearish_count = len([s for s in all_signals if s.get('direction') == 'bearish'])
        avg_strength = sum(s.get('strength', 0) for s in all_signals) / len(all_signals)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <h3 style="color: #00ff88; margin: 0;">🟢 {bullish_count}</h3>
                <p style="color: #00ff88; margin: 0;">BULLISH SIGNALS</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <h3 style="color: #ff0080; margin: 0;">🔴 {bearish_count}</h3>
                <p style="color: #ff0080; margin: 0;">BEARISH SIGNALS</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <h3 style="color: #ffaa00; margin: 0;">💪 {avg_strength:.2f}</h3>
                <p style="color: #ffaa00; margin: 0;">AVG STRENGTH</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_patterns = len(patterns)
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <h3 style="color: #00aaff; margin: 0;">🎯 {total_patterns}</h3>
                <p style="color: #00aaff; margin: 0;">PATTERN TYPES</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Enhanced pattern table
    pattern_rows = []
    pattern_emojis = {
        'doji': '🎯',
        'hammer': '🔨', 
        'engulfing': '🌟',
        'ma_crossover': '💎',
        'support_resistance': '🔷'
    }
    
    for pattern_name, signals in patterns.items():
        for signal in signals:
            emoji = pattern_emojis.get(pattern_name, '⭐')
            direction = signal.get('direction', 'neutral')
            
            # Direction styling
            if direction == 'bullish':
                direction_display = '🟢 BULLISH'
                color_class = 'color: #00ff88;'
            elif direction == 'bearish':
                direction_display = '🔴 BEARISH'
                color_class = 'color: #ff0080;'
            elif direction in ['support', 'resistance']:
                direction_display = f'🔷 {direction.upper()}'
                color_class = 'color: #00aaff;'
            else:
                direction_display = '🟡 NEUTRAL'
                color_class = 'color: #ffaa00;'
            
            pattern_rows.append({
                'Pattern': f"{emoji} {pattern_name.replace('_', ' ').title()}",
                'Direction': direction_display,
                'Strength': f"{signal.get('strength', 0):.2f}",
                'Price': f"${signal['price']:.4f}",
                'Time': signal['datetime'].strftime('%Y-%m-%d %H:%M'),
            })
    
    if pattern_rows:
        # Create enhanced DataFrame
        df_patterns = pd.DataFrame(pattern_rows)
        
        # Display with custom styling
        st.markdown("#### 📊 DETAILED SIGNAL MATRIX")
        st.dataframe(
            df_patterns,
            use_container_width=True,
            hide_index=True
        )
        
        # Signal sentiment analysis
        if all_signals:
            bullish_ratio = bullish_count / len(all_signals)
            bearish_ratio = bearish_count / len(all_signals)
            
            st.markdown("#### 🧠 NEURAL SENTIMENT ANALYSIS")
            
            if bullish_ratio > 0.6:
                sentiment = "🚀 STRONG BULLISH"
                sentiment_color = "#00ff88"
            elif bearish_ratio > 0.6:
                sentiment = "📉 STRONG BEARISH"
                sentiment_color = "#ff0080"
            elif bullish_ratio > bearish_ratio:
                sentiment = "🟢 MODERATE BULLISH"
                sentiment_color = "#00ff88"
            elif bearish_ratio > bullish_ratio:
                sentiment = "🔴 MODERATE BEARISH"
                sentiment_color = "#ff0080"
            else:
                sentiment = "🟡 NEUTRAL"
                sentiment_color = "#ffaa00"
            
            st.markdown(f"""
            <div style="text-align: center; margin: 1rem;">
                <h3 style="color: {sentiment_color}; font-family: 'Orbitron'; text-shadow: 0 0 10px {sentiment_color};">
                    {sentiment}
                </h3>
                <p style="color: #ffffff; font-family: 'Orbitron';">
                    Market Sentiment for {symbol}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Strength distribution
            strengths = [s.get('strength', 0) for s in all_signals]
            high_strength = len([s for s in strengths if s >= 0.7])
            medium_strength = len([s for s in strengths if 0.4 <= s < 0.7])
            low_strength = len([s for s in strengths if s < 0.4])
            
            st.markdown("#### ⚡ SIGNAL STRENGTH DISTRIBUTION")
            strength_col1, strength_col2, strength_col3 = st.columns(3)
            
            with strength_col1:
                st.markdown(f"""
                <div style="text-align: center; color: #00ff88;">
                    <h4>🔥 HIGH</h4>
                    <p>{high_strength} signals</p>
                </div>
                """, unsafe_allow_html=True)
            
            with strength_col2:
                st.markdown(f"""
                <div style="text-align: center; color: #ffaa00;">
                    <h4>⚡ MEDIUM</h4>
                    <p>{medium_strength} signals</p>
                </div>
                """, unsafe_allow_html=True)
            
            with strength_col3:
                st.markdown(f"""
                <div style="text-align: center; color: #ff4444;">
                    <h4>💫 LOW</h4>
                    <p>{low_strength} signals</p>
                </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()