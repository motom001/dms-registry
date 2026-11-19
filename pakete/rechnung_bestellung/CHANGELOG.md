# Änderungen

## 1.0.0

Nachfolger des Pakets **Rechnungen** (bis 1.3.0), ohne Umzug aus dem alten Paket – es gab nur eine Installation, und die wird neu aufgebaut.

- **Rechnung neu aufgebaut** (dms-registry #208): oben Rechnungssteller, Rechnungsempfänger, Status, Betrag, Rechnungsnummer, Rechnungsdatum, Fällig am, Bezahlt am und Bezahlt per; darunter *Einzelheiten* mit Betrifft, **Gehört zu Vertrag / Bestellung** (mehrfach und gemischt) und Steuerjahr, direkt darunter *Fahrzeug* und *Vermietung*; dann *Beträge im Einzelnen*, *Ausgangsrechnung*, *Kontierung*, *Positionen* und der neue Abschnitt **Archiv** (Verbleib Original, Gefundene Kundennummer, Gefundene Vertragskontonummer). Register nur noch *Rechnung*, **Dokumente** (statt Anlagen), *Verknüpfungen* und *Historie*; Lieferscheine stehen unter *Verknüpfungen*.
- **Entfallen:** Bemerkungen, Bezahlt von und der einzelne Umsatzsteuersatz mit Netto und Umsatzsteuer. „Kunden- oder Vertragsnummer“ heißt jetzt *Gefundene Kundennummer*. Am Betrag steht der Hinweis zur Gutschrift nur noch einmal.
- **Umsatzsteuer aufteilen** (#210): neuer Mappentyp **Steuerzeile** (Satz, Netto, Steuerbetrag, im Betrieb Steuerschlüssel) als Tabelle mit „+ Satz“ unter *Beträge im Einzelnen*. Das Paket rechnet einen leeren Steuerbetrag aus, summiert *Netto gesamt* und *Umsatzsteuer gesamt* und meldet als Hinweis, wenn beides nicht zum Bruttobetrag passt. Haben Positionen einen Satz, legt es je Satz eine Zeile „aus Positionen“ an und hält sie aktuell (Einstellung, eingeschaltet); änderst du so eine Zeile, gehört sie dir. Aus der E-Rechnung füllt Ablago die Zeilen erst, wenn der Kern die Aufteilung liefert.
- **Neuer Mappentyp Bestellung** (#211): Händler oder Lieferant, Bestellnummer, Bestelldatum, Betrag, Lieferstand, *Rücksendefrist bis* (Automatisierung „Rücksendefrist endet bald“, 3 Tage vorher, eingeschaltet), Betrifft und Gehört zu Vertrag; Bestätigungen als Dokumente. Lieferschein und Rechnung zeigen auf die Bestellung.
- Status, Summenprüfung der Positionen, „Als bezahlt markieren“ und die tägliche Prüfung wie in Rechnungen 1.3.0. Braucht **Ablago 0.248.0**.
