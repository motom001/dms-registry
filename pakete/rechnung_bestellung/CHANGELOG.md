# Änderungen

## 1.6.0

- **„Woran man ihn erkennt“ kürzer** (dms-registry #267): je Mappentyp vier bis sechs Wörter, die fast jedes Dokument dieses Typs enthält, statt langer Listen. Lange Listen sprachen bei Ablago oft gegen den richtigen Typ, weil jedes Dokument nur wenige ihrer Wörter enthält. Ein Update übernimmt den Text, solange ihr ihn nicht selbst geändert habt.

## 1.5.0

- **„Woran man ihn erkennt“** für jeden Mappentyp, Deutsch und Englisch (dms-registry #254): Was auf dem Papier steht – Überschriften, Begriffe, Nummern. Hilft Ablago beim Vorschlag „Wohin gehört das?“. Ein Update setzt den Text, solange ihr ihn nicht selbst geändert habt.

## 1.4.0

- **Steuerjahr aus „Bezahlt am“** (dms-registry #261): Für die Steuer zählt der Zahlungstag; Ablago schlägt das Steuerjahr daraus vor. „Bezahlt am“ wird aus dem Dokument gelesen. **Titel ohne Aussteller** (#258): „Rechnung: 03.04.2026 – 214,00 €“ statt „: 03.04.2026 …“, ebenso Bestellung und Lieferschein. Braucht Ablago ab 0.321.0.

## 1.3.0

- **Sprechendere Titel** (dms-registry #256, Thomas 24.11.2026): Rechnung und Bestellung (Nummer, Datum, Betrag), Lieferschein (Nummer). Lange Namen werden auf 25 Zeichen gekürzt. Gilt für neue Installationen – Ablago übernimmt eine geänderte Titel-Vorlage beim Update nicht.

## 1.2.2

- **Betrifft** einer Rechnung kann auch ein **Behandlungsfall** aus dem Paket Gesundheit sein (dms-registry #226) – Arztrechnungen stehen dann im Verlauf des Behandlungsfalls. Ablago bietet den Typ an, sobald das Paket Gesundheit installiert ist.

## 1.2.1

- **Mehrzahl** für die Mappentypen (dms-registry #223): Listen zeigen jetzt z. B. „12 Rechnungen“ statt „12 × Rechnung“ (ab Ablago 0.302.0, ältere ignorieren es). Ein Update setzt die Mehrzahl nur, wo du noch keine eingetragen hast.
- **Treffendere Symbole** der Ansichten aus den 259 Symbolen von Ablago 0.304 (dms-registry #230): Rechnungen (Beleg mit Euro), Offen (Sanduhr), Unterwegs (Lastwagen), Lieferscheine (Klemmbrett). Ältere Ablago-Versionen zeigen ein neues Symbol einfach nicht.

## 1.2.0

- Ansichten: *Rechnungen und Bestellungen*, darunter je Mappentyp eine Ansicht mit Symbol – *Rechnungen* (mit *Offen*), *Bestellungen* (mit *Unterwegs*) und *Lieferscheine*. *Dieses Jahr* entfällt. Ein Update nimmt keine Ansichten weg: In bestehenden Ablagen bleiben weggefallene Ansichten stehen, bis du sie löschst (Thomas, 20.11.2026).

## 1.1.0

- **Steuerjahr und Konto aus dem Paket Finanzen** (dms-registry #212): Rechnungen und Bestellungen hängt jetzt von Finanzen 1.0.0 ab. *Steuerjahr* zeigt auf das Steuerjahr aus Finanzen (bisher optional aus Haushalt), neben *Bezahlt per* gibt es das Feld **Konto** – von welchem Konto bezahlt oder auf welches eingegangen.

## 1.0.0

Nachfolger des Pakets **Rechnungen** (bis 1.3.0), ohne Umzug aus dem alten Paket – es gab nur eine Installation, und die wird neu aufgebaut.

- **Rechnung neu aufgebaut** (dms-registry #208): oben Rechnungssteller, Rechnungsempfänger, Status, Betrag, Rechnungsnummer, Rechnungsdatum, Fällig am, Bezahlt am und Bezahlt per; darunter *Einzelheiten* mit Betrifft, **Gehört zu Vertrag / Bestellung** (mehrfach und gemischt) und Steuerjahr, direkt darunter *Fahrzeug* und *Vermietung*; dann *Beträge im Einzelnen*, *Ausgangsrechnung*, *Kontierung*, *Positionen* und der neue Abschnitt **Archiv** (Verbleib Original, Gefundene Kundennummer, Gefundene Vertragskontonummer). Register nur noch *Rechnung*, **Dokumente** (statt Anlagen), *Verknüpfungen* und *Historie*; Lieferscheine stehen unter *Verknüpfungen*.
- **Entfallen:** Bemerkungen, Bezahlt von und der einzelne Umsatzsteuersatz mit Netto und Umsatzsteuer. „Kunden- oder Vertragsnummer“ heißt jetzt *Gefundene Kundennummer*. Am Betrag steht der Hinweis zur Gutschrift nur noch einmal.
- **Umsatzsteuer aufteilen** (#210): neuer Mappentyp **Steuerzeile** (Satz, Netto, Steuerbetrag, im Betrieb Steuerschlüssel) als Tabelle mit „+ Satz“ unter *Beträge im Einzelnen*. Das Paket rechnet einen leeren Steuerbetrag aus, summiert *Netto gesamt* und *Umsatzsteuer gesamt* und meldet als Hinweis, wenn beides nicht zum Bruttobetrag passt. Haben Positionen einen Satz, legt es je Satz eine Zeile „aus Positionen“ an und hält sie aktuell (Einstellung, eingeschaltet); änderst du so eine Zeile, gehört sie dir. Aus der E-Rechnung füllt Ablago die Zeilen erst, wenn der Kern die Aufteilung liefert.
- **Neuer Mappentyp Bestellung** (#211): Händler oder Lieferant, Bestellnummer, Bestelldatum, Betrag, Lieferstand, *Rücksendefrist bis* (Automatisierung „Rücksendefrist endet bald“, 3 Tage vorher, eingeschaltet), Betrifft und Gehört zu Vertrag; Bestätigungen als Dokumente. Lieferschein und Rechnung zeigen auf die Bestellung.
- Status, Summenprüfung der Positionen, „Als bezahlt markieren“ und die tägliche Prüfung wie in Rechnungen 1.3.0. Braucht **Ablago 0.248.0**.
