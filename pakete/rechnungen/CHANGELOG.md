# Änderungen

## 1.2.1

- **Status wird wieder berechnet** (dms-registry #209): Das Paket las die Mappe in einer älteren Form der Antwort von Ablago, fand darin keine Werte und schrieb deshalb nie einen Status – weder nach dem Speichern noch nach „Als bezahlt markieren“. Auch die Summenprüfung beim Speichern einer Rechnung rechnete so ins Leere. Jetzt rechnet es beides wie gedacht; die tägliche Prüfung war nicht betroffen.
- **Kein stilles „unverändert“ mehr bei Konflikten:** Hat sich die Mappe zwischen Lesen und Speichern geändert (409), liest das Paket sie einmal neu und rechnet noch einmal. Klappt auch das nicht, steht es als Fehler im Verlauf des Pakets. Ist die Mappe beim Speichern weg (404), steht eine Zeile im Protokoll.

## 1.2.0

- **Aktion „Als bezahlt markieren“** im Menü *Mappe* an der Rechnung (dms-registry #162, Ablago #1039): fragt das Datum (heute vorgeschlagen) und trägt *Bezahlt am* ein; den Status rechnet das Paket danach neu. Ist die Rechnung schon bezahlt, steht das im Menü.
- Braucht **Ablago 0.245.3** (Aktionen ab 0.245.0; 0.245.1 und 0.245.2 lehnten Pakete mit Anzeige-Bedingungen ab, 0.245.3 kennt Bedingungen auf Fahrzeuge und Vermietung, auch wenn die Pakete fehlen).

## 1.1.0

- **Rechnungen aus Fahrzeuge und Vermietung ziehen um** (dms-registry #163, Ablago #1041): Beim Installieren oder Aktualisieren von Rechnungen ziehen die Mappen der Typen *Werkstattrechnung* (Fahrzeuge bis 1.x) und *Ausgabe Mietobjekt* (Vermietung bis 1.x) in die Rechnung – mit allen Werten, Dokumenten, Verknüpfungen, Ansichten und Rechten. Ablago zeigt vorher, was wohin geht; was nicht passt, steht danach in einer Notiz an der Mappe.
  - *Werkstattrechnung:* Fahrzeug → Betrifft, Werkstatt → Rechnungssteller; Kilometerstand und Arbeiten im Abschnitt *Fahrzeug*.
  - *Ausgabe Mietobjekt:* Mietobjekt → Betrifft (eine zusätzlich eingetragene Wohnung steht in der Notiz), Firma → Rechnungssteller, Art → Kostenart (was es dort nicht gibt, z. B. „Modernisierung“, steht in der Notiz), Umlagefähig, Steuerjahr und Notiz bleiben.
  - Der Umbau läuft nur einzeln (nicht zusammen mit anderen Paketen) und nur mit „Gesamte Verwaltung“; „Vorher sichern“ ist vorausgewählt.
- Braucht **Ablago 0.243.0**.

## 1.0.1

- **Installieren repariert:** Ohne das Paket Fahrzeuge bzw. Vermietung brach Ablago 0.238–0.244 die Installation ab („Der Verweis „fahrzeuge:fahrzeug“ lässt sich nicht auflösen“). Die Abschnitte *Fahrzeug* und *Vermietung* fragen jetzt mit „zeigt auf eine Mappe vom Typ …“ (`zeigtAufTyp`), das fehlende Pakete überspringt. Sonst unverändert.

## 1.0.0

- Neu (dms-registry #161, Etappe 15): Mappentyp **Rechnung** für Rechnungen, Quittungen, Kassenbons, Gutschriften und Erstattungen – eingehend und ausgehend. Oben Rechnungssteller, Betrag (mit Minus für Gutschriften), Rechnungsdatum, fällig am, bezahlt am, *Status*; darunter *Wozu* (betrifft Fahrzeug, Immobilie, Wohnung, Anschaffung oder Vertrag; gehört zu Vertrag; Steuerjahr) und eingeklappt die *Einzelheiten*. **Beträge im Einzelnen** zeigen sich nur, wenn Ablago beruflich genutzt wird, **Ausgangsrechnung** nur, wenn wir der Rechnungssteller sind, **Fahrzeug** und **Vermietung** nur, wenn die Rechnung ein Fahrzeug bzw. ein Mietobjekt oder eine Wohnung betrifft. Positionen als Tabelle mit „+ Position“.
- Neu: **Lieferschein** (Lieferant, Lieferdatum, Nummern, vollständig erhalten, gehört zu Rechnung) und **Rechnungsposition** (gehört immer zu ihrer Rechnung, erscheint nur dort).
- **Berechnung:** Status in Worten („offen – fällig am …“, „überfällig seit …“, „bezahlt am …“, „Gutschrift – noch nicht erhalten“), bei jeder Änderung und jeden Morgen (Automatisierung „Rechnungen täglich prüfen“, gleich eingeschaltet). An Positionen Gesamtpreis (wenn leer: Menge × Einzelpreis) und Umsatzsteuer. **Summenprüfung:** Passen die Positionen nicht zum Betrag, steht an der Rechnung ein ruhiger Hinweis mit beiden Zahlen – Speichern hindert er nie, Rundung bis 1 Cent je Position zählt nicht.
- Ansichten *Rechnungen*, *Offen*, *Dieses Jahr*, *Lieferscheine*; gleichbedeutende Wörter (Umsatzsteuer/Mehrwertsteuer …).
- Kurzanleitung „So nutzt du es“ (dms-registry #164).
- Braucht Basis ab 1.7.0, Verträge ab 1.0.0 und **Ablago 0.238.0**. Herausgeber `app.ablago`.
