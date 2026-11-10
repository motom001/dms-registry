# Änderungen

## 1.0.0

- Neu (dms-registry #166, Etappe 16): Paket **Compliance** – Selbstkontrolle mit Verfahrensdokumentation. Unterstützt die Dokumentation, ist kein Zertifikat und keine Rechts- oder Steuerberatung.
- **Verfahren:** je Bereich eine Mappe, die ihr beschreibt (Allgemeines, Belegeingang und Scannen, Ablage, Zugang und Berechtigungen, Betrieb, Sicherung, Unveränderbarkeit, Datenschutz, Betriebsprüfung). Es zeigt sich nur der Abschnitt des gewählten Bereichs; was nur im Betrieb zählt, nur bei beruflicher Nutzung. Lesen alle, ändern die Verwaltung.
- **Konfiguration:** je Bereich und Monat eine Mappe, angelegt vom Paket – Status aktuell/abgelöst, Änderung in Worten, Vorgänger und Nachfolger, JSON-Datei je Stand als Version mit Prüfwert (SHA-256). Nur die Gesamte Verwaltung liest sie, nur das Paket legt sie an.
- **Nachweise:** ein Bericht je Monat mit Zahlen je Bereich und Benutzern zum Stichtag; verpasste Monate holt das Paket nach. Lesen nur die Gesamte Verwaltung.
- Automatisierung **„Konfiguration und Nachweise festhalten“** (jeden Morgen, gleich eingeschaltet); Einstellungen **„was zählt“** je Bereich mit dem abgestimmten Vorschlag.
- Aufbewahrung: Verfahren und Konfiguration 2 Jahre (beruflich 10), Nachweise 2 Jahre; die Frist eines aktuellen Stands läuft noch nicht.
- Ansichten *Aktueller Stand*, *Verfahren*, *Nachweise*, *Alle Konfigurationen*. Kein Netz.
- Braucht Ablago ab 0.230.0 (vorläufig).
