# Plotly Symbole für Marker (pattern_styles)

## Grundformen
- `circle` - Kreis
- `square` - Quadrat
- `diamond` - Raute
- `cross` - Kreuz                                                  -> für double top
- `x` - X-Form                                                     -> für macd_crossover zuverlässig als erstes crossover ?
- `triangle-up` - Dreieck nach oben
- `triangle-down` - Dreieck nach unten
- `triangle-left` - Dreieck nach links
- `triangle-right` - Dreieck nach rechts
- `triangle-ne` - Dreieck nach nordost
- `triangle-se` - Dreieck nach südost
- `triangle-sw` - Dreieck nach südwest
- `triangle-nw` - Dreieck nach nordwest

## Offene Varianten
- `circle-open` - Offener Kreis
- `square-open` - Offenes Quadrat
- `diamond-open` - Offene Raute
- `cross-open` - Offenes Kreuz
- `x-open` - Offenes X                                             -> für ma_crossover (späte Bestätigung macd_crossover?) 
- `triangle-up-open` - Offenes Dreieck nach oben
- `triangle-down-open` - Offenes Dreieck nach unten

## Spezialformen
- `star` - Stern
- `hexagon` - Sechseck
- `pentagon` - Fünfeck
- `hourglass` - Sanduhr
- `diamond-tall` - Hohe Raute
- `diamond-wide` - Breite Raute
- `star-diamond` - Stern-Raute
- `star-square` - Stern-Quadrat
- `star-triangle-up` - Stern-Dreieck nach oben
- `star-triangle-down` - Stern-Dreieck nach unten
- `arrow-up` - Pfeil nach oben
- `arrow-down` - Pfeil nach unten
- `arrow-left` - Pfeil nach links
- `arrow-right` - Pfeil nach rechts

## Kombinierte Formen
- `circle-dot` - Kreis mit Punkt
- `square-dot` - Quadrat mit Punkt
- `diamond-dot` - Raute mit Punkt
- `triangle-up-dot` - Dreieck nach oben mit Punkt
- `triangle-down-dot` - Dreieck nach unten mit Punkt
- `octagon` - Achteck
- `hexagram` - Hexagramm
- `star-triangle-up-open` - Offener Stern-Dreieck nach oben         -> für h&s
- `star-triangle-down-open` - Offener Stern-Dreieck nach unten      -> für inverse h&s
- `star-square-open` - Offener Stern-Quadrat
- `star-diamond-open` - Offener Stern-Raute

Diese Symbole werden in der `create_professional_chart`-Funktion in `app.py` verwendet, um die verschiedenen Pattern-Typen in den Charts visuell darzustellen.