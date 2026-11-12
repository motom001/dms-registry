# Änderungen

## 1.3.0

- **Umzug mit Fristen** (Ablago #1125): Versicherungen aus *Haushalt* bekommen beim Umzug gleich die üblichen Werte der Vertragsart *Versicherung* (12 Monate Laufzeit, verlängert sich um 12 Monate, 3 Monate zum Laufzeitende), Mietverträge aus *Vermietung* die der Vertragsart *Miete* (läuft unbefristet weiter, 3 Monate zum Monatsende). Gesetzt wird nur, was leer ist; danach rechnet das Paket *Kündigen bis* gleich richtig.
- Verträge aus *Haushalt* behalten ihre Art als Bezeichnung, die Vertragsart wählst du danach. Alle zehn Arten aus *Haushalt* gibt es als Vertragsart.
- Braucht **Ablago 0.248.0**.

## 1.2.0

- **Aktion „Vorlage hinzufügen“** im Menü *Mappe* am Vertrag (dms-registry #160, Ablago #1039): öffnet „Brief aus Vorlage“ mit den Vorlagen dieses Pakets an der Vertragsart und legt das fertige PDF in den Vertrag – mit deinen Rechten, ohne eigenen Code. Solange keine Vertragsart gewählt ist, steht im Menü, warum die Aktion noch nicht geht.
- **Vorlage „Kündigung“** an jeder mitgelieferten Vertragsart: Anschrift des Anbieters, Bezeichnung, Vertragsnummer, Kundennummer, „zum nächstmöglichen Termin, das ist der …“ (das berechnete *Frühestens zu Ende am*), Bitte um Bestätigung, Platz für die Unterschrift. Ein Muster ohne Gewähr. Bei einer bestehenden Installation kommen die Vorlagen an unveränderte Vertragsarten dazu.
- Wenn du die Kündigung abgeschickt hast, trag *Gekündigt am* ein – dann rechnet das Paket das Ende.
- Braucht **Ablago 0.245.3** (Aktionen ab 0.245.0; 0.245.1 und 0.245.2 lehnten Pakete mit Anzeige-Bedingungen ab).

## 1.1.0

- **Verträge aus Haushalt und Vermietung ziehen um** (dms-registry #163, Ablago #1041): Beim Installieren oder Aktualisieren von Verträge ziehen die Mappen der Typen *Vertrag* und *Versicherung* (Haushalt bis 1.x) und *Mietvertrag* (Vermietung bis 1.x) in den Vertrag – mit allen Werten, Dokumenten, Verknüpfungen, Ansichten und Rechten. Ablago zeigt vorher, was wohin geht; was nicht passt, steht danach in einer Notiz an der Mappe. Ist Verträge noch nicht installiert, wird der Vertrag aus Haushalt zum Vertrag dieses Pakets (gleiche Id) – dann gibt es auch keinen Namenskonflikt „Vertrag“.
  - *Vertrag (Haushalt):* Vertragspartner → Anbieter, Art → Bezeichnung (die Vertragsart wählst du danach), Kündigungsfrist („3 Monate …“) → Kündigungsfrist als Zeitraum (der ganze Text steht zusätzlich in der Notiz). „Mindestlaufzeit bis“ und „Kündigen bis“ stehen in der Notiz – trag Mindestlaufzeit und „Danach“ ein, dann rechnet das Paket *Kündigen bis* selbst.
  - *Versicherung (Haushalt):* Vertragsart Versicherung, Bezeichnung „Versicherung“, Versicherer → Anbieter, Art → Versicherung (Haftpflicht, Kfz …), Versicherungsnummer → Vertragsnummer, Versichert → Versicherte Personen, Beitrag → Betrag, Hauptfälligkeit bleibt.
  - *Mietvertrag (Vermietung):* Vertragsart Miete, Bezeichnung „Mietvertrag“, Wohnung → Betrifft, Mieter → Kunde, Ende → Vertragsende, Miete und Kaution in den Abschnitt Miete; der Stand („läuft“ …) steht in der Notiz, den Status rechnet das Paket.
  - Der Umbau läuft nur einzeln (nicht zusammen mit anderen Paketen) und nur mit „Gesamte Verwaltung“; „Vorher sichern“ ist vorausgewählt.
- Neu am Vertrag: **Betrifft** (unter *Weiteres*) – wofür der Vertrag ist: Fahrzeug, Wohnung, Mietobjekt, Immobilie oder Anschaffung, sobald das Paket dazu installiert ist. Gleiche Kennung wie bei Rechnungen.
- **Berechnung:** Ist ein Vertrag gekündigt, steht keine Kündigungsfrist, aber ein Vertragsende darin (so kommen gekündigte Mietverträge aus Vermietung 1.x an), gilt das Vertragsende als Ende – sonst endete er am Tag der Kündigung.
- **Kunde** nimmt jetzt mehrere Personen oder Organisationen (z. B. alle Mieter). Bei einer bestehenden Installation bleibt das Feld, wie es ist.
- Braucht **Ablago 0.243.0**.

## 1.0.1

- **Installieren repariert:** Ablago 0.238–0.244 brach die Installation mit „Abschnitt „Miete“: Das Feld „art“ gibt es nicht (mehr)“ ab. Grund: Die Vertragsart stand in `mappentypen.yaml` nach dem Vertrag, und Ablago legt den Verweis darauf erst im zweiten Durchgang an. Jetzt steht die Vertragsart vorn. Inhalt und Berechnung sind unverändert.

## 1.0.0

- Neu (dms-registry #159, Etappe 15): Mappentyp **Vertrag** für alle Verträge – zu Hause und im Betrieb. Oben das Wichtigste (Bezeichnung, Anbieter, Vertragsart, Zuständig, Kündigen bis, Status), darunter eingeklappt Vertragsparteien, Laufzeit und Kündigung, Kosten und Weiteres. **Abschluss** zeigt sich nur, wenn Anbieter oder Kunde eine eigene Organisation ist, **Miete** und **Versicherung** nur bei dieser Vertragsart.
- Neu: Mappentyp **Vertragsart** mit üblicher Laufzeit und Kündigungsfrist, Register *Vorlagen* und *Verträge*. Mitgeliefert: Strom, Gas, Wasser, Internet, Mobilfunk, Streaming, Zeitschrift, Mitgliedschaft, Miete, Versicherung, Sonstiges – die Fristen sind übliche Werte als Vorschlag, ohne Gewähr. Wer am Vertrag die Vertragsart wählt, bekommt ihre Fristen in leere Felder vorgeschlagen.
- **Berechnung:** Bei jeder Änderung und jeden Morgen (Automatisierung „Verträge täglich prüfen“) rechnet das Paket Status, Kündigen bis, frühestes Ende, nächste Verlängerung, Ende, Laufzeit in Monaten und den Betrag pro Monat aus. Es schreibt nur diese Felder und nur, wenn sich etwas ändert; hat inzwischen ein Mensch dasselbe Feld geändert, gewinnt der Mensch. „Kündigen bis“ gibt es nur, wenn ein Laufzeitende wartet – im unbefristeten Teil sagt der Status, wann der Vertrag frühestens endet.
- Mitgelieferte Automatisierungen: **„Verträge täglich prüfen“** (gleich eingeschaltet, 5 Uhr, „Paket nach Zeitplan ausführen“) und **„Vertrag rechtzeitig kündigen“** (aus): 30 Tage vor „Kündigen bis“ eine Aufgabe an *Zuständig*, sonst an den, der den Vertrag angelegt hat.
- Ansichten *Verträge*, *Kündigen bald*, *Gekündigt*, *Vertragsarten*; drei Beispiele (Strom, Handy, Haftpflicht).
- Kurzanleitung „So nutzt du es“ (dms-registry #164).
- Braucht Basis ab 1.7.0 und **Ablago 0.238.0**. Herausgeber `app.ablago`.
