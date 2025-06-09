# 🚀 Pattern Pilot v2 - Installation & Setup

## **1. Quick Install (5 Minuten)**

```bash
# Neues Projekt erstellen
mkdir pattern_pilot_v2
cd pattern_pilot_v2

# Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Dependencies installieren
pip install -r requirements.txt

# TA-Lib installieren (kann tricky sein)
# Windows: Download wheels von https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# pip install TA_Lib-0.4.28-cp311-cp311-win_amd64.whl

# Mac: 
# brew install ta-lib
# pip install talib

# Linux:
# sudo apt-get install libta-lib-dev
# pip install talib
```

## **2. Projekt-Struktur erstellen**

```bash
# Core Module
mkdir -p core config utils
touch core/__init__.py config/__init__.py utils/__init__.py

# Files von Artifacts kopieren
# - requirements.txt (root)
# - app_streamlit.py (root) 
# - core/market_engine.py
```

## **3. App starten**

```bash
streamlit run app_streamlit.py
```

## **4. Features Overview**

### ✅ **Was funktioniert sofort:**
- 🔥 **130+ Exchanges** (Binance, Coinbase, Kraken, etc.)
- 📊 **150+ Pattern** (alle talib Candlestick + Custom)
- 📈 **Interactive Charts** (Zoom, Pan, Hover)
- 💾 **Auto-Caching** (5min cache)
- 🎯 **Real-time Symbols** (live Symbol-Liste)

### 🎯 **Pattern Types verfügbar:**
- **Candlestick:** Doji, Hammer, Engulfing, Morning Star, etc.
- **Trend:** MA Crossovers, Bollinger Squeezes
- **Custom:** Beliebig erweiterbar

### 📱 **Mobile-Optimiert:**
- Responsive plotly charts
- Touch-friendly UI
- Schnelle Performance

## **5. vs Pattern Pilot v1**

| Feature | v1 (Alt) | v2 (Neu) |
|---------|----------|----------|
| **APIs** | 2 Custom | 130+ ccxt |
| **Patterns** | ~10 Handmade | 150+ talib |
| **Charts** | matplotlib | plotly (interactive) |
| **Code Lines** | ~3000 | ~300 |
| **Setup Time** | 2 Stunden | 5 Minuten |
| **Maintenance** | High | Low |
| **Reliability** | Custom bugs | Battle-tested |

## **6. Erweiterte Features (Optional)**

### **Redis Cache (statt dict):**
```bash
pip install redis
# Redis server installieren
```

### **More Patterns:**
```python
# In market_engine.py erweitern:
'marubozu': talib.CDLMARUBOZU,
'spinning_top': talib.CDLSPINNINGTOP,
'takuri': talib.CDLTAKURI,
# ... 50+ mehr verfügbar
```

### **Custom Indicators:**
```python
def detect_rsi_divergence(self, df):
    rsi = talib.RSI(df['close'].values)
    # Custom divergence logic
    return signals
```

## **7. Deployment**

### **Streamlit Cloud:**
```bash
# requirements.txt committen
git add .
git commit -m "Pattern Pilot v2"
git push

# Auf streamlit.io deployen
```

### **Docker:**
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y libta-lib-dev
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["streamlit", "run", "app.py"]
```

## **8. Nächste Schritte**

1. **Phase 1:** Basic setup testen
2. **Phase 2:** Pattern-Detection erweitern  
3. **Phase 3:** Alerts/Notifications hinzufügen
4. **Phase 4:** Portfolio-Tracking
5. **Phase 5:** Backtesting mit zipline

**🎯 Ergebnis:** Ein Profi-Tool in Bruchteil der Zeit!