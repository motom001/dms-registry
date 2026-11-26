# Änderungen

## 1.2.0

- **Wohin gehört das? – Nähe statt Menge** (dms-registry #265): Das Paket schlägt den Mappentyp vor, dem das Dokument am **ähnlichsten** ist, nicht mehr den, von dem es die meisten ähnlichen Mappen gibt. Je Typ zählen die drei nächsten Mappen (die zweite halb, die dritte ein Viertel); eine sehr nahe Mappe schlägt viele mittelmäßige. So gewinnt ein großer Typ wie Kontoauszug nicht mehr gegen die eine fast gleiche Mappe eines seltenen Typs.
- **Große Typen ausgleichen:** Ab Ablago 0.328.0 bekommt das Paket die Zahl der Mappen je Typ (DMS #1682) und dämpft Typen mit weit mehr Mappen als üblich. Mit älterem Ablago wie bisher ohne Ausgleich.
- **Sicherheit und Begründung:** Die Sicherheit kommt aus der Nähe der nächsten Mappe und dem Vorsprung vor den übrigen Typen statt aus dem Anteil („6 von 10“). Die Begründung nennt die Nähe in Worten („Sehr ähnlich zu einer Mappe in Wartung“), weiter ohne Titel fremder Mappen.
- Gemessen am Satz „Lebensläufe“ (501 Dokumente der Reihe nach, offline mit `tests/satz_vergleich.mjs`): richtiger Typ vorn 45,3 % → 60,0 %.

## 1.1.3

- README: Das Paket arbeitet nur hier – die Ausnahmen für Dienste im Netz gelten für es nicht (dms-registry #262).

## 1.1.2

- Kurzbeschreibung in Alltagssprache, ohne Fachwörter (dms-registry #80).

## 1.1.1

- Kurzanleitung „So nutzt du es“ im Katalog und nach der Installation in Ablago (dms-registry #198, motom001/dms#1047).
- Manifest: Herausgeber `app.ablago`.

## 1.1.0

- **Wohin gehört das?** – neue Schnittstelle `dms:klassifizieren` (dms-registry #142, Ablago #939): Auf der Seite *Dokument übernehmen* schlägt das Paket vor, zu welchem Mappentyp neue Post gehört – aus den ähnlichsten schon abgelegten Mappen („8 von 10 ähnlichen Mappen liegen in Rechnung“), bis zu drei Typen mit Sicherheit. Ablago rechnet die ähnlichen Mappen selbst – nur solche, die die Person **und** das Paket lesen dürfen, nur aus Mappentypen, die in Frage kommen und für KI-Dienste zugelassen sind – und gibt dem Paket nur Typ und Ähnlichkeit, **keine Titel und keine Inhalte**. Die Begründung nennt deshalb nur Zahlen und den Mappentyp.
- Ohne ähnliche Mappen (leere Ablage) gibt es keinen Vorschlag statt eines geratenen; bei wenigen Treffern ist die Sicherheit geringer.
- Kein Netz, kein Sprachmodell, das Modell wird dafür nicht geladen; die Grenzen des Läufers (256 MB je Aufruf) reichen.
- Braucht **Ablago ab 0.226.0**. Beim Update zeigt Ablago das neue Recht *Mappentyp vorschlagen* und lässt es dich bestätigen.

## 1.0.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.0.0

- Erste Fassung: Vektoren aus dem Volltext mit static-similarity-mrl-multilingual-v1 (256 Dimensionen, 8 Bit), Vektor eines Suchbegriffs für die Suche des DMS, Tokenizer von bert-base-multilingual-uncased in C.
