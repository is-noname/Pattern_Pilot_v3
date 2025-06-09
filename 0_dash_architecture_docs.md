# 🚀 Pattern Pilot - Dash Architecture Documentation

## 📋 Inhaltsverzeichnis
1. [Architektur-Überblick](#architektur-überblick)
2. [Dateistruktur](#dateistruktur)
3. [Dash-Grundlagen](#dash-grundlagen)
4. [Component-System](#component-system)
5. [Callback-System](#callback-system)
6. [Styling-System](#styling-system)
7. [Neue Features hinzufügen](#neue-features-hinzufügen)
8. [Pattern-Engine Integration](#pattern-engine-integration)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architektur-Überblick

```
┌─────────────────────────────────────────────────┐
│                 Frontend (Dash)                 │
├─────────────────────────────────────────────────┤
│  app_dash.py     │  Layout + Callbacks          │
│  ├─ get_layout() │  UI Structure                │
│  ├─ callbacks    │  User Interactions           │
│  └─ styling      │  CSS + Professional Theme    │
├─────────────────────────────────────────────────┤
│               Business Logic                    │
├─────────────────────────────────────────────────┤
│  core/market_engine.py │ Trading Data + Patterns│
│  ├─ ccxt integration   │ 130+ Exchanges         │
│  ├─ talib patterns     │ 150+ Indicators        │
│  └─ caching system     │ Performance            │
├─────────────────────────────────────────────────┤
│  config/settings.py    │ Configuration          │
└─────────────────────────────────────────────────┘
```

**Separation of Concerns:**
- **Frontend:** Dash handles UI, interactions, visualization
- **Business Logic:** Market engine handles data, analysis
- **Configuration:** Centralized settings management

---

## 📁 Dateistruktur

```
pattern_pilot_v3/
├── app_dash.py                 # 🎯 Main Dash Application
├── requirements_dash.txt       # Dependencies
├── core/
│   ├── __init__.py
│   ├── market_engine.py       # 🔥 Trading Engine (unchanged)
│   └── market_engine_lite.py  # TA-Lib free version
├── config/
│   ├── __init__.py
│   └── settings.py            # Configuration
└── docs/
    └── DASH_ARCHITECTURE.md   # This file
```

**Key Files:**
- **`app_dash.py`:** Complete Dash application (655 lines)
- **`core/market_engine.py`:** Unchanged from Streamlit version
- **`config/settings.py`:** All configuration centralized

---

## ⚛️ Dash-Grundlagen

### Was ist Dash?
Dash = **Flask** (Backend) + **React** (Frontend) + **Plotly** (Charts)

```python
# Basic Dash Structure
import dash
from dash import html, dcc, Input, Output

# Initialize app
app = dash.Dash(__name__)

# Define layout (what user sees)
app.layout = html.Div([...])

# Define callbacks (what happens on interaction)
@app.callback(Output(...), Input(...))
def callback_function(input_value):
    return output_value

# Run app
app.run(debug=True)
```

### Dash vs. Streamlit

| Feature | Streamlit | Dash |
|---------|-----------|------|
| **Layout Control** | Limited | Full Control |
| **Performance** | Reruns everything | Targeted updates |
| **Styling** | CSS hacks | Native CSS/HTML |
| **Callbacks** | Sequential | Event-driven |
| **Professional Look** | Difficult | Easy |

---

## 🧩 Component-System

### HTML Components (`html.*`)
```python
html.Div([...])          # Container
html.H1("Title")         # Heading
html.P("Text")           # Paragraph
html.Button("Click")     # Button
html.Span("Inline")      # Inline text
```

### Core Components (`dcc.*`)
```python
dcc.Dropdown(options=[], value="")    # Dropdown selector
dcc.Input(type="number", value=100)   # Input field
dcc.Graph(figure=fig)                 # Plotly chart
dcc.Store(id="data")                  # Data storage
```

### Our Custom Components

**1. Header Bar** (`render_header()`)
```python
# Location: app_dash.py, line 160-180
def render_header():
    """Professional header with exchange status"""
    return html.Div([
        html.Div("Professional Trading Terminal"),
        html.Div(exchange_indicators),  # Live exchange status
        html.Div(current_time)          # Real-time clock
    ], className="header-bar")
```

**2. Trading Controls** (`render_main_interface()`)
```python
# Location: app_dash.py, line 200-250
# Symbol, Timeframe, Candles, Exchange, Analyze Button
html.Div([
    dcc.Dropdown(id="symbol-dropdown", ...),
    dcc.Dropdown(id="timeframe-dropdown", ...),
    # ... more controls
], className="controls-row")
```

**3. News Sidebar** (`render_news_panel()`)
```python
# Location: app_dash.py, line 280-320
def render_news_panel():
    """Professional news feed"""
    return html.Div([
        html.H3("Market News & Analysis"),
        html.Div(news_items)
    ], className="news-sidebar")
```

---

## 🔄 Callback-System

### Callback-Grundlagen
```python
@app.callback(
    Output("output-component", "property"),  # What gets updated
    Input("input-component", "property"),    # What triggers update
    State("state-component", "property")     # Additional data (optional)
)
def callback_function(input_value, state_value):
    # Process input
    result = some_processing(input_value, state_value)
    return result  # Goes to Output
```

### Main Analysis Callback
```python
# Location: app_dash.py, line 430-460
@app.callback(
    [Output("main-chart", "figure"),           # Updates chart
     Output("pattern-summary", "children")],   # Updates pattern info
    Input("analyze-btn", "n_clicks"),          # Triggered by button
    [Input("symbol-dropdown", "value"),        # Uses these values
     Input("timeframe-dropdown", "value"),
     Input("limit-input", "value"),
     Input("exchange-dropdown", "value")]
)
def analyze_symbol(n_clicks, symbol, timeframe, limit, exchange):
    # 1. Get data from market engine
    df = market_engine.get_ohlcv(symbol, timeframe, limit, exchange)
    
    # 2. Detect patterns
    patterns = market_engine.detect_patterns(df)
    
    # 3. Create chart and summary
    chart = create_professional_chart(df, patterns, symbol, timeframe)
    summary = create_pattern_summary(patterns, len(df))
    
    return chart, summary
```

### Callback-Trigger-Logic
```python
# Only runs when button is clicked
if not n_clicks:
    return create_placeholder_chart(), html.Div()

# Button was clicked -> run analysis
```

---

## 🎨 Styling-System

### CSS Architecture
```python
# Location: app_dash.py, line 20-150
app.index_string = '''
<style>
/* 1. Global Theme */
body { background: #1a1a1a; color: #e0e0e0; }

/* 2. Layout Components */
.header-bar { background: #2a2a2a; }
.main-container { display: flex; }
.trading-panel { flex: 1; }
.news-sidebar { width: 300px; }

/* 3. Interactive Elements */
.analyze-btn { background: #404040; }
.Select-control { background: #2a2a2a; }

/* 4. Chart Styling */
.chart-container { border: 1px solid #404040; }
</style>
'''
```

### Color Scheme
```css
/* Professional Trading Terminal Colors */
Background:    #1a1a1a  (Main dark)
Panels:        #2a2a2a  (Lighter dark)
Borders:       #404040  (Gray borders)
Text:          #e0e0e0  (Light gray)
Success:       #4CAF50  (Green)
Error:         #f44336  (Red)
Warning:       #ff9800  (Orange)
```

### Component-Specific Styling
```python
# Inline styles for dynamic content
html.Div("Content", style={
    "color": "#4CAF50",
    "fontWeight": "bold",
    "textAlign": "center"
})

# CSS classes for static styling
html.Div("Content", className="status-metric")
```

---

## ➕ Neue Features hinzufügen

### 1. Neue UI-Komponente hinzufügen

**Beispiel: Portfolio-Tracker hinzufügen**

```python
# Step 1: Create component function
def render_portfolio_panel():
    """Portfolio overview panel"""
    return html.Div([
        html.H3("Portfolio"),
        html.Div(id="portfolio-content"),
        dcc.Store(id="portfolio-data")  # Data storage
    ], className="portfolio-panel")

# Step 2: Add to main layout (in get_layout())
# Add after trading_panel:
portfolio_panel = render_portfolio_panel()

# Step 3: Update main container
html.Div([trading_panel, portfolio_panel, news_sidebar], 
         className="main-container")
```

### 2. Neue Callback hinzufügen

```python
# Step 1: Define callback
@app.callback(
    Output("portfolio-content", "children"),
    Input("symbol-dropdown", "value")  # Trigger
)
def update_portfolio(selected_symbol):
    # Your logic here
    portfolio_data = get_portfolio_data(selected_symbol)
    return create_portfolio_display(portfolio_data)

# Step 2: Add CSS styling
.portfolio-panel {
    background: #2a2a2a;
    border: 1px solid #404040;
    padding: 16px;
}
```

### 3. Neue Chart-Features

```python
# Add to create_professional_chart() function
# Location: app_dash.py, line 520-600

# Example: Add moving averages
ma_20 = df['close'].rolling(20).mean()
ma_50 = df['close'].rolling(50).mean()

fig.add_trace(
    go.Scatter(
        x=df['datetime'], 
        y=ma_20,
        name="MA20",
        line=dict(color="#ff9800", width=1)
    ),
    row=1, col=1
)
```

---

## 🔧 Pattern-Engine Integration

### How Market Engine Works
```python
# Location: core/market_engine.py (unchanged from Streamlit)

# 1. Data Fetching
df = market_engine.get_ohlcv(symbol, timeframe, limit, exchange)
# Uses ccxt to get data from 130+ exchanges

# 2. Pattern Detection  
patterns = market_engine.detect_patterns(df)
# Uses talib for 150+ technical indicators

# 3. Result Format
{
    'doji': [
        {
            'index': 45,
            'datetime': datetime(...),
            'price': 67890.12,
            'strength': 0.8,
            'direction': 'neutral',
            'pattern': 'doji'
        }
    ],
    'hammer': [...],
    # ... more patterns
}
```

### Adding New Patterns

**Option 1: Add to market_engine.py**
```python
# In detect_patterns() method, add:
patterns['new_pattern'] = self._detect_new_pattern(df)

def _detect_new_pattern(self, df):
    """Your custom pattern logic"""
    signals = []
    # Pattern detection logic
    return signals
```

**Option 2: Add TA-Lib pattern**
```python
# In candlestick_patterns dict:
'new_talib_pattern': talib.CDLNEWPATTERN,
```

### Displaying New Patterns

**1. Add to pattern colors** (line 560):
```python
pattern_colors = {
    'doji': '#ff9800',
    'hammer': '#4CAF50',
    'new_pattern': '#purple',  # Add here
}
```

**2. Update pattern summary** (line 630):
Pattern summary automatically includes all detected patterns.

---

## 💡 Best Practices

### 1. Code Organization
```python
# ✅ Good: Separate functions
def render_header(): pass
def render_main_interface(): pass  
def render_news_panel(): pass

# ❌ Bad: Everything in one function
def get_layout():
    # 500 lines of mixed code
```

### 2. Callback Design
```python
# ✅ Good: Specific outputs
@app.callback(
    Output("chart", "figure"),
    Input("analyze-btn", "n_clicks")
)

# ❌ Bad: Multiple unrelated outputs  
@app.callback(
    [Output("chart", "figure"), Output("news", "children")],
    Input("analyze-btn", "n_clicks")
)
```

### 3. Error Handling
```python
def analyze_symbol(n_clicks, ...):
    if not n_clicks:
        return create_placeholder_chart(), html.Div()
    
    try:
        # Main logic
        return success_result
    except Exception as e:
        return create_error_chart(str(e)), error_summary
```

### 4. Performance
```python
# ✅ Use dcc.Store for data sharing
dcc.Store(id="market-data", data=df.to_dict())

# ✅ Cache expensive operations
@lru_cache(maxsize=128)
def expensive_calculation(symbol, timeframe):
    pass

# ✅ Minimal chart updates
# Only update what changed, not entire chart
```

### 5. Styling
```python
# ✅ Use CSS classes for reusable styles
html.Div(className="metric-card")

# ✅ Use inline styles for dynamic content
style={"color": "#4CAF50" if bullish else "#f44336"}

# ❌ Avoid mixing CSS and inline extensively
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. Callback not triggering**
```python
# Check: Is Input ID correct?
Input("wrong-id", "value")  # ❌
Input("symbol-dropdown", "value")  # ✅

# Check: Is component in layout?
# Component must exist in layout before callback
```

**2. Charts not updating**
```python
# Check: Return correct figure object
return fig  # ✅ plotly figure
return df   # ❌ wrong type

# Check: Figure has data
if df.empty:
    return create_placeholder_chart()
```

**3. Styling not applied**
```python
# Check: CSS selector specificity
.my-class { color: red; }           # Low specificity
.main-container .my-class { ... }   # Higher specificity

# Check: CSS location in index_string
app.index_string = '''<style>...</style>'''  # ✅
# External CSS files need special setup in Dash
```

**4. Layout not rendering**
```python
# Check: app.layout is set
app.layout = get_layout()  # ✅ Must be there

# Check: Function returns valid HTML
def get_layout():
    return html.Div([...])  # ✅
    return "string"         # ❌ Invalid
```

### Debug Mode
```python
# Enable debug mode for detailed errors
app.run(debug=True)

# Check browser console (F12) for JavaScript errors
# Check terminal for Python errors
```

### Performance Debugging
```python
# Add timing to callbacks
import time

@app.callback(...)
def callback_function(...):
    start = time.time()
    result = expensive_operation()
    print(f"Callback took {time.time() - start:.2f}s")
    return result
```

---

## 🚀 Next Steps

### Planned Features (from setup_v3.md)
1. **Phase 4: Portfolio Tracking** → Add portfolio panel
2. **Phase 5: Backtesting** → Add backtesting interface  
3. **Real-time Updates** → WebSocket integration
4. **Alerts System** → Notification components

### Architecture Improvements
1. **Component Library** → Reusable UI components
2. **State Management** → Better data flow
3. **Testing** → Unit tests for callbacks
4. **Documentation** → Auto-generated API docs

---

## 📚 Resources

- **Dash Documentation:** https://dash.plotly.com/
- **Plotly Charts:** https://plotly.com/python/
- **Our Market Engine:** `core/market_engine.py`
- **Configuration:** `config/settings.py`

---

*Last Updated: Pattern Pilot v3.0 - Professional Terminal Edition*