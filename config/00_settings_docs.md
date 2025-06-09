Modulübersicht: settings.py

1. Importierte Module und Komponenten
   `os`
   `typing`: `Dict`, `List`

2. Globale Konfigurationsobjekte

* `EXCHANGE_CONFIG`: API-Limits und Sandbox-Modus pro Exchange
* `PATTERN_CONFIG`: Aktivierte Patterns, Perioden für technische Indikatoren, Visualisierungsstile
* `CACHE_CONFIG`: Zwischenspeicherung mit TTL und Backend-Typ
* `CHART_CONFIG`: Darstellungsoptionen für Charts (Farben, Layout)
* `UI_CONFIG`: Einstellungen für App-Layout, Default-Symbole & Timeframes
* `DEV_CONFIG`: Debug- & Entwicklungsoptionen
* `API_KEYS`: Umgebungsvariablen für API-Schlüssel
* `MOBILE_CONFIG`: Mobile-spezifische Optimierungen

3. Funktionen

```python
get_exchange_config(exchange_name: str) -> Dict
Holt Konfiguration für spezifischen Exchange.
Rückgabe: Dict mit rateLimit, enableRateLimit, sandbox (falls definiert)

get_enabled_patterns() -> List[str]
Gibt Liste der aktivierten Candlestick-Pattern zurück.
Rückgabe: Liste von Pattern-Namen

is_debug_mode() -> bool
Prüft, ob Debug-Modus per Umgebungsvariable aktiv ist.
Rückgabe: True/False
```

Keine Klassen oder Methoden enthalten.
Möchtest du ein Klassendiagramm, Ablaufdiagramm oder dieses Konfigurationsmodul in anderen Dateien nachverfolgen?
