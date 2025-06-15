# 📝 Pattern Pilot Code-Kommentierungs-Standard

## 1️⃣ Datei-Header
Jede Datei beginnt mit einem Header, der den Dateinamen und eine kurze Beschreibung enthält:

```python
# dateiname.py - Kurze, prägnante Beschreibung der Datei
```

## 2️⃣ Klassen-Dokumentation
Klassen werden mit einem Docstring dokumentiert, der ein Emoji, eine Kurzbeschreibung und ggf. weitere Details enthält:

```python
class ClassName:
    """
    🚀 Kurze Zusammenfassung der Klasse
    
    Detailliertere Beschreibung
    Weitere wichtige Informationen
    """
```

## 3️⃣ Methoden-Dokumentation
### Komplexe Methoden
Für komplexe Methoden mit eigener Logik:

```python
def complex_method(self, param1, param2):
    """
    🎯 Hauptzweck der Methode
    
    Detaillierte Beschreibung der Funktionalität
    
    Args:
        param1: Beschreibung von param1
        param2: Beschreibung von param2
        
    Returns:
        Beschreibung des Rückgabewerts
    """
```

### Einfache Methoden
Für einfache oder selbsterklärende Methoden:

```python
def simple_method(self):
    """Kurze Beschreibung in einer Zeile"""
```

### Überladene/Überschriebene Methoden
Für Methoden, die identisch mit anderen sind:

```python
def overridden_method(self):
    """Same wie in ParentClass"""
```

## 4️⃣ Sektions-Kommentare

### Hauptsektionen
Für primäre Codeblöcke oder Hauptbereiche einer Datei:

```python
# ===== HAUPTSEKTIONSNAME =====
# Hier kommen relevante Code-Blöcke
```

### Funktionale Sektionen
Für logisch zusammengehörige Funktionsgruppen mit Emoji-Kennzeichnung:

```python
# 📡 Funktionaler Bereich
# Hier kommen relevante Code-Blöcke
```

### Untersektionen
Für sekundäre Gruppierungen innerhalb von Hauptsektionen:

```python
## Untersektionsname
# Relevanter Code
```

### Datei-spezifische Sektionen
#### Python-Dateien
```python
# --- Imports ---
# --- Konstanten ---
# --- Hilfsfunktionen ---
# --- Hauptklassen ---
# --- Callback-Funktionen ---
```

#### CSS-Dateien
```css
/* ===== KOMPONENTENNAME ===== */
/* --- Grundlegende Stile --- */
/* --- Hover-Zustände --- */
/* --- Responsive Anpassungen --- */
```

#### Konfigurationsdateien
```python
# 📡 Exchange Konfiguration
# 🎯 Pattern Konfiguration
# 💾 Cache Konfiguration
# 📊 Chart Konfiguration
# 🎨 UI Konfiguration
```

### Trennlinien für lange Dateien
Für zusätzliche visuelle Trennung in langen Dateien:

```python
#########################################
# HAUPTABSCHNITT
#########################################

# Code...

#----------------------------------------
# Unterabschnitt
#----------------------------------------
```

## 5️⃣ Inline-Kommentare
Für spezifische Erklärungen innerhalb des Codes:

```python
value = x * y  # Berechnung der Fläche
```

## 6️⃣ Emoji-Guide
Verwende konsistente Emojis für bestimmte Arten von Kommentaren:

- 🚀 - Hauptklassen, Core-Funktionalität
- 🎯 - Methoden mit spezifischem Zweck
- ⚠️ - Warnungen, Probleme
- ✅ - Erfolgreiche Operationen
- ❌ - Fehler, Fehlschläge
- 📡 - Netzwerk/API-Operationen
- 💾 - Speicher/Cache-Operationen
- 📊 - Datenanalyse/Visualisierung
- 🔄 - Wiederholte Operationen, Loops
- 🔧 - Konfigurationen, Einstellungen
- 🕯️ - Candlestick-spezifische Operationen
- 💡 - Tipps, Ideen

## 7️⃣ TODO-Kommentare
Für zukünftige Entwicklungsaufgaben:

```python
# TODO: Beschreibung der zu erledigenden Aufgabe
```

## 8️⃣ FIXME-Kommentare
Für bekannte Probleme, die behoben werden müssen:

```python
# FIXME: Beschreibung des Problems
```

## 9️⃣ Kommentare zum Verständnis von Algorithmen
Für komplexe Algorithmen (wie Pattern-Detection):

```python
# Berechnung des Bollinger Squeeze:
# 1. Berechne Bandbreite (BB upper - BB lower)
# 2. Normalisiere durch Preis
# 3. Vergleiche mit gleitendem Durchschnitt
```

## 🔟 Debugging-Kommentare
Temporäre Kommentare für Debugging (sollten vor Commit entfernt werden):

```python
# DEBUG: print(f"Variable x: {x}")
```

---

## Allgemeine Grundsätze

1. **Klarheit über Kürze**: Kommentare sollen verständlich sein, auch wenn sie etwas länger werden.
2. **Code-Logik erklären**: Nicht WAS der Code tut, sondern WARUM er es tut.
3. **Regelmäßige Updates**: Kommentare bei Code-Änderungen aktualisieren.
4. **Konsistenz**: Gleicher Stil im gesamten Projekt.
5. **Dokumentation von Edge Cases**: Besondere Randfälle und ihre Behandlung dokumentieren.
6. **Use TODO comments**: Als Notiz für offene Aufgaben anfügen.

## Vermeiden

1. **Unnötige Kommentare**: Nicht offensichtliche Dinge kommentieren.
2. **Veraltete Kommentare**: Keine Kommentare, die nicht mehr zum Code passen.
3. **Auskommentierter Code**: Keine Code-Blöcke auskommentiert lassen.
4. **Übermäßige Kommentierung**: Nicht jede Zeile braucht einen Kommentar.
