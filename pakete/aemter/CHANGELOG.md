# Änderungen

## 1.4.0

- **„Woran man ihn erkennt“ kürzer** (dms-registry #267): je Mappentyp vier bis sechs Wörter, die fast jedes Dokument dieses Typs enthält, statt langer Listen. Lange Listen sprachen bei Ablago oft gegen den richtigen Typ, weil jedes Dokument nur wenige ihrer Wörter enthält. Ein Update übernimmt den Text, solange ihr ihn nicht selbst geändert habt.
- **Aus dem Dokument gefüllt:** Art bei Urkunde, Bescheinigung und Bescheid – steht der Wert wörtlich im Dokument, schlägt Ablago ihn vor.

## 1.3.0

- **„Woran man ihn erkennt“** für jeden Mappentyp, Deutsch und Englisch (dms-registry #254): Was auf dem Papier steht – Überschriften, Begriffe, Nummern. Hilft Ablago beim Vorschlag „Wohin gehört das?“. Ein Update setzt den Text, solange ihr ihn nicht selbst geändert habt. Widerspruch und Ausweis lesen Art, Nummer und Daten aus dem Dokument.

## 1.2.0

- **Zeitraum am Bescheid** (dms-registry #261): Steht „gilt vom … bis …“ im Bescheid, landen die Daten in „Gilt ab“ und „Gilt bis“. Braucht Ablago ab 0.321.0.

## 1.1.0

- **Sprechendere Titel** (dms-registry #256, Thomas 24.11.2026): Antrag (mit Behörde statt „an“), Bescheid, Widerspruch. Lange Namen werden auf 25 Zeichen gekürzt. Gilt für neue Installationen – Ablago übernimmt eine geänderte Titel-Vorlage beim Update nicht.

## 1.0.0

- Erste Fassung (dms-registry #225): **Antrag**, **Bescheid** und **Widerspruch** für die Post vom Amt, **Ausweis**, **Urkunde** und **Bescheinigung** für die eigenen Papiere – Deutsch und Englisch, mit Ansichten, Beispielen der Familie Muster, Automatisierungen (Einspruchsfrist, Begründung, Ausweis läuft ab, Antrag nachfragen), dem Rundgang „Ausweis ablegen“ (bisher in Haushalt) und zwei Tipps.
- Ersetzt „Ausweis & Urkunde“ aus Haushalt (bis 3.x) und die Bescheid-Felder am Steuerjahr aus Finanzen (bis 1.x). Einen Umzug vorhandener Mappen gibt es nicht.
