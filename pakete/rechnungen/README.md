# Rechnungen

Rechnungen, Quittungen, Kassenbons, Gutschriften und Erstattungen – **eingehend und ausgehend**, mit Lieferscheinen und Positionen. Das Paket zeigt, was **offen, bezahlt oder überfällig** ist, und meldet ruhig, wenn die Positionen nicht zum Betrag passen.

## Inhalt

| Mappentyp | wofür | wichtige Felder |
| --- | --- | --- |
| Rechnung | jede Rechnung, Quittung, Gutschrift | Rechnungssteller (`von`), Betrag (Minus = Gutschrift), Rechnungsdatum, fällig am, bezahlt am, *Status*, betrifft, gehört zu Vertrag, Steuerjahr |
| Lieferschein | was geliefert wurde | Lieferant, Lieferdatum, Lieferschein- und Bestellnummer, vollständig erhalten, gehört zu Rechnung |
| Rechnungsposition | eine Zeile einer Rechnung – erscheint nur an ihrer Rechnung | Nr., Beschreibung, Menge, Einheit, Einzelpreis, Gesamtpreis, Umsatzsteuersatz, *Umsatzsteuer*, Artikelnummer |

### Rechnung

| Teil | Felder | zu sehen |
| --- | --- | --- |
| oben | Rechnungssteller, Betrag, Rechnungsdatum, Fällig am, Bezahlt am, *Status* | immer |
| Wozu | Betrifft (Fahrzeug, Immobilie, Mietobjekt, Wohnung, Anschaffung, Vertrag – je nachdem, welche Pakete installiert sind), Gehört zu Vertrag, Steuerjahr | immer |
| Einzelheiten | Rechnungsnummer, Kunden-/Vertragsnummer, Bezahlt per, Bezahlt von, Rechnungsempfänger (`an`, leer = wir) | eingeklappt |
| Beträge im Einzelnen | Netto, Umsatzsteuersatz, Umsatzsteuer, Skonto, Skonto bis | nur, wenn Ablago beruflich genutzt wird |
| Ausgangsrechnung | Zahlungseingang am, Mahnstufe, interne Nummer | nur, wenn der Rechnungssteller eine eigene Organisation ist |
| Fahrzeug | Kilometerstand, Arbeiten | nur, wenn die Rechnung ein Fahrzeug betrifft |
| Vermietung | Umlagefähig, Kostenart | nur bei Mietobjekt oder Wohnung |
| Positionen | Tabelle der Rechnungspositionen mit „+ Position“ | immer |

Register: *Rechnung*, *Anlagen*, *Lieferscheine*, *Verknüpfungen*, *Historie*.

## So rechnet das Paket

- **Status:** „offen – fällig am 15.11.2026“, „überfällig seit 01.11.2026“, „bezahlt am 09.11.2026“; bei Gutschriften „Gutschrift – noch nicht erhalten“ bzw. „Gutschrift erhalten am …“; bei Ausgangsrechnungen zählt der Zahlungseingang. Neu bei jeder Änderung und jeden Morgen über die mitgelieferte Automatisierung **„Rechnungen täglich prüfen“** (gleich eingeschaltet, änderbar unter Automatisierungen).
- **Positionen:** Ist der Gesamtpreis leer, füllt das Paket Menge × Einzelpreis ein – was du selbst einträgst, bleibt. Mit Umsatzsteuersatz gelten die Preise netto, das Paket rechnet die Umsatzsteuer aus.
- **Summenprüfung:** Ergeben die Positionen (mit Umsatzsteuer) etwas anderes als der Betrag, steht an der Rechnung „Die Positionen ergeben 118,97 €, die Rechnung sagt 120,80 €.“ Bis 1 Cent je Position zählt als Rundung. Der Hinweis verschwindet, sobald es passt; Speichern hindert er nie.

## Als bezahlt markieren

An der Rechnung trägt **Mappe → Als bezahlt markieren** *Bezahlt am* ein – heute oder ein Datum, das du wählst. Den Status rechnet das Paket danach neu. Ist die Rechnung schon bezahlt, steht das im Menü.

## Einstellungen

| Einstellung | Vorgabe | Bedeutung |
| --- | --- | --- |
| Positionen mit dem Betrag vergleichen | an | Aus: kein Hinweis an der Rechnung. |

## Umzug aus Fahrzeuge und Vermietung

Bis Fahrzeuge 1.x und Vermietung 1.x brachten eigene Typen *Werkstattrechnung* und *Ausgabe Mietobjekt* mit. Ab Rechnungen 1.1.0 ziehen sie beim **Installieren oder Aktualisieren von Rechnungen** hierher (Ablago 0.243.0, „Umbau“): Ablago zeigt vorher, wie viele Mappen umziehen und welche Werte wohin gehen; nach deiner Bestätigung (nur mit „Gesamte Verwaltung“) laufen sie in einem Zug um. Was nicht in ein Feld passt, steht danach in einer **Notiz** an der Mappe. Reihenfolge: erst Verträge, dann Rechnungen (je allein), danach Haushalt, Fahrzeuge und Vermietung auf 2.0.0.

## Voraussetzungen

- Ablago ab 0.245.3: Aktionen im Menü „Mappe“, Umbau, Prozent, negative Beträge, Anzeige-Bedingungen, mehrere Ziele, berechnete Felder, Hinweise, Tabelle, „Paket nach Zeitplan ausführen“, „gehört immer zu“ und eigene Organisation (Etappe 15).
- Pakete Basis ab 1.7.0 und Verträge ab 1.0.0. Fahrzeuge, Haus, Vermietung und Haushalt sind nicht nötig – sind sie installiert, kann *Betrifft* auf ihre Mappen zeigen.

## Rechte und Netzwerkzugriff

- **Mappen lesen:** Rechnung, Rechnungsposition · **Mappen anlegen und ändern:** Rechnung (nur *Status*), Rechnungsposition (nur *Umsatzsteuer* und leere Gesamtpreise).
- **Hinweise an Mappen setzen** (dms:hinweise) – nur an Rechnungen, nur zur Summe.
- Keine Dokumente, **kein Zugriff auf Netzwerk und Internet**.
- Reagiert auf: `mappe.angelegt`, `mappe.geaendert` (Rechnungen, Positionen), `zeitplan.ausgefuehrt` (Automatisierung „Rechnungen täglich prüfen“).

## Entwickeln

| Datei | Inhalt |
| --- | --- |
| [`code/rechnung.h`](code/rechnung.h) | Status, Positionen, Summenprüfung – ohne Ablago testbar |
| [`code/rechnungen.cpp`](code/rechnungen.cpp) | Ereignisse, Lesen und Schreiben über die API, Hinweis |
| [`tests/rechnung_test.cpp`](tests/rechnung_test.cpp) | läuft nativ in `code/bauen.sh` |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | das gebaute Modul gegen eine Nachbildung von Ablago |

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Rechnungen“ im Titel.
