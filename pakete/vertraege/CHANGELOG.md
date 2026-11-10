# Änderungen

## 1.0.0

- Neu (dms-registry #159, Etappe 15): Mappentyp **Vertrag** für alle Verträge – zu Hause und im Betrieb. Oben das Wichtigste (Bezeichnung, Anbieter, Vertragsart, Zuständig, Kündigen bis, Status), darunter eingeklappt Vertragsparteien, Laufzeit und Kündigung, Kosten und Weiteres. **Abschluss** zeigt sich nur, wenn Ablago beruflich genutzt wird, **Miete** und **Versicherung** nur bei dieser Vertragsart.
- Neu: Mappentyp **Vertragsart** mit üblicher Laufzeit und Kündigungsfrist, Register *Vorlagen* und *Verträge*. Mitgeliefert: Strom, Gas, Wasser, Internet, Mobilfunk, Streaming, Zeitschrift, Mitgliedschaft, Miete, Versicherung, Sonstiges – die Fristen sind übliche Werte als Vorschlag, ohne Gewähr. Wer am Vertrag die Vertragsart wählt, bekommt ihre Fristen in leere Felder vorgeschlagen.
- **Berechnung:** Bei jeder Änderung und jeden Morgen (Automatisierung „Verträge täglich prüfen“) rechnet das Paket Status, Kündigen bis, frühestes Ende, nächste Verlängerung, Ende, Laufzeit in Monaten und den Betrag pro Monat aus. Es schreibt nur diese Felder und nur, wenn sich etwas ändert; hat inzwischen ein Mensch dasselbe Feld geändert, gewinnt der Mensch. „Kündigen bis“ gibt es nur, wenn ein Laufzeitende wartet – im unbefristeten Teil sagt der Status, wann der Vertrag frühestens endet.
- Mitgelieferte Automatisierungen: **„Verträge täglich prüfen“** (gleich eingeschaltet, 5 Uhr, „Paket nach Zeitplan ausführen“) und **„Vertrag rechtzeitig kündigen“** (aus): 30 Tage vor „Kündigen bis“ eine Aufgabe an *Zuständig*, sonst an den, der den Vertrag angelegt hat.
- Ansichten *Verträge*, *Kündigen bald*, *Gekündigt*, *Vertragsarten*; drei Beispiele (Strom, Handy, Haftpflicht).
- Braucht Basis ab 1.7.0 und Ablago ab 0.230.0 (vorläufig – die Version steht fest, sobald die Kern-Teile der Etappe 15 gemergt sind).
