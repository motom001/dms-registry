# Änderungen

## 1.0.1

- **Installieren repariert:** Ohne das Paket Fahrzeuge bzw. Vermietung brach Ablago 0.238–0.244 die Installation ab („Der Verweis „fahrzeuge:fahrzeug“ lässt sich nicht auflösen“). Die Abschnitte *Fahrzeug* und *Vermietung* fragen jetzt mit „zeigt auf eine Mappe vom Typ …“ (`zeigtAufTyp`), das fehlende Pakete überspringt. Sonst unverändert.

## 1.0.0

- Neu (dms-registry #161, Etappe 15): Mappentyp **Rechnung** für Rechnungen, Quittungen, Kassenbons, Gutschriften und Erstattungen – eingehend und ausgehend. Oben Rechnungssteller, Betrag (mit Minus für Gutschriften), Rechnungsdatum, fällig am, bezahlt am, *Status*; darunter *Wozu* (betrifft Fahrzeug, Immobilie, Wohnung, Anschaffung oder Vertrag; gehört zu Vertrag; Steuerjahr) und eingeklappt die *Einzelheiten*. **Beträge im Einzelnen** zeigen sich nur, wenn Ablago beruflich genutzt wird, **Ausgangsrechnung** nur, wenn wir der Rechnungssteller sind, **Fahrzeug** und **Vermietung** nur, wenn die Rechnung ein Fahrzeug bzw. ein Mietobjekt oder eine Wohnung betrifft. Positionen als Tabelle mit „+ Position“.
- Neu: **Lieferschein** (Lieferant, Lieferdatum, Nummern, vollständig erhalten, gehört zu Rechnung) und **Rechnungsposition** (gehört immer zu ihrer Rechnung, erscheint nur dort).
- **Berechnung:** Status in Worten („offen – fällig am …“, „überfällig seit …“, „bezahlt am …“, „Gutschrift – noch nicht erhalten“), bei jeder Änderung und jeden Morgen (Automatisierung „Rechnungen täglich prüfen“, gleich eingeschaltet). An Positionen Gesamtpreis (wenn leer: Menge × Einzelpreis) und Umsatzsteuer. **Summenprüfung:** Passen die Positionen nicht zum Betrag, steht an der Rechnung ein ruhiger Hinweis mit beiden Zahlen – Speichern hindert er nie, Rundung bis 1 Cent je Position zählt nicht.
- Ansichten *Rechnungen*, *Offen*, *Dieses Jahr*, *Lieferscheine*; gleichbedeutende Wörter (Umsatzsteuer/Mehrwertsteuer …).
- Kurzanleitung „So nutzt du es“ (dms-registry #164).
- Braucht Basis ab 1.7.0, Verträge ab 1.0.0 und **Ablago 0.238.0**. Herausgeber `app.ablago`.
