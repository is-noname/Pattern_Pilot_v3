# Projekt Standards

## Design System

### Farbschema
- **Background:** #1a1a1a (dark) / #f5f5f5 (light)
- **Text:** #f5f5f5 (dark mode) / #1a1a1a (light mode)
- **Akzent:** Canto Green #06fc99 für interaktive Elemente
- **Grautöne:** #333, #555, #777 für Abstufungen

### Typografie
- **Font Stack:** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Größen:** 16px base, 1.5 line-height
- **Hierarchie:** H1 2.5rem, H2 2rem, H3 1.5rem

### Layout
- **Container:** max-width 800px, zentriert
- **Layout-System:** Flexbox und CSS Grid responsive
- **Breakpoints:** Mobile 320px, Tablet 768px, Desktop 1200px
- **Spacing:** 8px Grid (8, 16, 24, 32, 48px)
- **Mobile-First:** Immer von klein nach groß entwickeln

## Component Standards

### Buttons
```css
.btn {
  padding: 12px 24px;
  border-radius: 8px;
  background: #06fc99;
  color: #1a1a1a;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 44px; /* Touch-Target */
}

.btn:hover { opacity: 0.8; }
.btn:focus { outline: 2px solid #06fc99; }
```

### Input Fields
```css
.input {
  padding: 12px 16px;
  border: 1px solid #333;
  border-radius: 6px;
  background: #1a1a1a;
  color: #f5f5f5;
  font-size: 16px; /* iOS Zoom Prevention */
}

.input:focus {
  outline: none;
  border-color: #06fc99;
  box-shadow: 0 0 0 2px rgba(6, 252, 153, 0.2);
}
```

### Drag & Drop Zones
```css
.drop-zone {
  border: 2px dashed #06fc99;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  transition: all 0.2s ease;
}

.drop-zone.dragover {
  background: rgba(6, 252, 153, 0.1);
}

.drop-zone[aria-dropeffect="move"]:focus {
  outline: 2px solid #06fc99;
}
```

### Code Blocks
```css
.code-block {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  background: #2a2a2a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  white-space: pre;
  font-size: 14px;
  line-height: 1.4;
}

pre, code {
  font-family: inherit;
}
```

## Code Conventions

### File Naming
- **HTML/CSS/JS:** kebab-case (`user-profile.html`, `app-utils.js`)
- **Images:** kebab-case (`hero-banner.jpg`)
- **Komponenten:** PascalCase Ordner, kebab-case Dateien
- **Skripte:** kebab-case Dateienamen

### CSS Organization
```css
/* Inline im <head> - keine externen Bibliotheken */
/* 1. Reset/Base */
/* 2. Layout */
/* 3. Components */
/* 4. Utilities */
/* 5. Media Queries */
```

### JavaScript Standards
```javascript
'use strict';

// ES6 Module Pattern
// Event-driven Architektur
// Klare Funktionsnamen: getUserData(), validateForm()
// Konstanten: UPPERCASE_SNAKE_CASE
// Variablen: camelCase
```

### HTML Structure
```html
<!DOCTYPE html>
<html lang="de">
<head>
  <!-- Styles inline im <head> -->
</head>
<body>
  <header></header>
  <main></main>
  <footer></footer>
</body>
</html>
```

## Accessibility Requirements

### Pflicht-Standards
- **WCAG AA Level:** Mindestkontrast 4.5:1
- **Keyboard Navigation:** Tab-Reihenfolge logisch
- **Touch Targets:** Minimum 44px x 44px
- **Screen Reader:** ARIA-Labels wo nötig
- **Focus Indicators:** Immer sichtbar

### Semantic HTML
```html
<button type="button">Aktion</button> <!-- nie <div onclick> -->
<label for="email">E-Mail</label> <!-- immer mit for -->
<input id="email" type="email"> <!-- passende input types -->
```

## Performance Standards

### Optimierung
- **Images:** WebP format, lazy loading
- **CSS:** Critical Path inline, rest async
- **JavaScript:** Module bundling, Tree shaking
- **Loading:** Under 3s auf 3G Verbindung

### Mobile Optimierung
- **Touch-First:** Große Touch-Targets
- **Viewport:** `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **iOS Safari:** -webkit-appearance: none für Custom Inputs

## Content Guidelines

### Sprache
- **Deutsch:** Hauptsprache für alle Texte
- **Du-Form:** Direkte Ansprache
- **Kurz & präzise:** Keine Füllwörter
- **Aktiv statt passiv:** "Klicke hier" statt "Hier kann geklickt werden"

### Error Messages
```
Fehler: E-Mail-Adresse ungültig
Erfolg: Daten gespeichert
Info: Noch 3 Zeichen bis Minimum
```

## Quality Gates

### Code Review Checklist
- [ ] Responsive auf allen Breakpoints
- [ ] Keyboard-Navigation funktioniert
- [ ] Screen Reader Test bestanden
- [ ] Performance unter 3s Loading
- [ ] Cross-Browser getestet (Safari iOS, Chrome, Firefox)

### Testing Requirements
- **HTML Validation:** W3C konform
- **Accessibility:** axe-core oder Wave
- **Performance:** Lighthouse Score >90
- **Mobile:** Real Device Testing auf iOS

## File Structure
```
/
├── index.html
├── /assets/
│   ├── /images/ (optimized WebP)
│   ├── /icons/ (SVG preferred)
│   └── /fonts/ (WOFF2)
├── /components/ (reusable parts)
└── /docs/ (documentation)
```

## Browser Support
- **Primary:** Safari iOS 15+, Chrome 100+
- **Secondary:** Firefox 100+, Edge 100+
- **Mobile:** iOS Safari priority
- **Fallbacks:** Graceful degradation für ältere Browser