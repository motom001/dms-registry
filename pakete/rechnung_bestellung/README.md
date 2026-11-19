# Rechnungen und Bestellungen

Rechnungen, Quittungen, Kassenbons, Gutschriften und Erstattungen – **eingehend und ausgehend** – dazu Bestellungen, Lieferscheine und Positionen. Das Paket zeigt, was **offen, bezahlt oder überfällig** ist, teilt die Umsatzsteuer nach Sätzen auf und meldet ruhig, wenn die Summen nicht zum Betrag passen.

Es ist der Nachfolger des Pakets **Rechnungen**. Einen Umzug aus dem alten Paket gibt es nicht: Rechnungen hatte nur eine Installation, und die wird neu aufgebaut.

## Inhalt

| Mappentyp | wofür | wichtige Felder |
| --- | --- | --- |
| Rechnung | jede Rechnung, Quittung, Gutschrift | Rechnungssteller, Rechnungsempfänger, *Status*, Betrag (Minus = Gutschrift), Rechnungsnummer, Rechnungsdatum, Fällig am, Bezahlt am, Bezahlt per |
| Bestellung | ein Einkauf von der Bestellung bis zur Lieferung, online oder im Betrieb | Händler oder Lieferant, Bestellnummer, Bestelldatum, Betrag, Lieferstand (bestellt, versandt, angekommen, teilweise, zurückgeschickt), **Rücksendefrist bis** (erinnert 3 Tage vorher), Betrifft, Gehört zu Vertrag |
| Lieferschein | was geliefert wurde | Lieferant, Lieferdatum, Lieferschein- und Bestellnummer, Gehört zu Bestellung, vollständig erhalten, Gehört zu Rechnung |
| Rechnungsposition | eine Zeile einer Rechnung – erscheint nur an ihrer Rechnung | Nr., Beschreibung, Menge, Einheit, Einzelpreis, Gesamtpreis, Umsatzsteuersatz, *Umsatzsteuer*, Steuerschlüssel (nur beruflich), Artikelnummer |
| Steuerzeile | Umsatzsteuer zu einem Satz – erscheint nur an ihrer Rechnung | Satz, Netto, Steuerbetrag, Steuerschlüssel (nur beruflich), Herkunft (von Hand, aus Positionen, aus E-Rechnung) |

### Rechnung

| Teil | Felder | zu sehen |
| --- | --- | --- |
| oben | Rechnungssteller · Rechnungsempfänger (leer = wir) · *Status*; Betrag · Rechnungsnummer · Rechnungsdatum; Fällig am · Bezahlt am · Bezahlt per | immer |
| Einzelheiten | Betrifft (Fahrzeug, Immobilie, Mietobjekt, Wohnung, Anschaffung, Vertrag – je nachdem, welche Pakete installiert sind), **Gehört zu Vertrag / Bestellung** (mehrfach, auch gemischt), Steuerjahr | immer |
| Fahrzeug | Kilometerstand, Arbeiten | wenn die Rechnung ein Fahrzeug betrifft |
| Vermietung | Umlagefähig, Kostenart | bei Mietobjekt oder Wohnung |
| Beträge im Einzelnen | **Umsatzsteuer aufteilen** (Steuerzeilen mit „+ Satz“), *Netto gesamt*, *Umsatzsteuer gesamt*, Skonto, Skonto bis | nur, wenn Ablago beruflich genutzt wird; eingeklappt |
| Ausgangsrechnung | Zahlungseingang am, Mahnstufe, interne Nummer | wenn der Rechnungssteller eine eigene Organisation ist |
| Kontierung | Kostenstelle, Kostenträger, Sachkonto – Auswahl aus dem Paket [Kontierung](../kontierung/), ohne es bleiben die Felder leer | nur beruflich; eingeklappt |
| Positionen | Tabelle der Rechnungspositionen mit „+ Position“ | immer |
| Archiv | Verbleib Original, **Gefundene Kundennummer**, **Gefundene Vertragskontonummer** – so, wie sie auf dem Beleg standen | eingeklappt |

Register: *Rechnung*, *Dokumente*, *Verknüpfungen* (dort auch Lieferscheine), *Historie*.

### Bestellung

Eine Bestellung ist in Ablago **kein Vertrag**: Verträge laufen (Laufzeit, Verlängerung, Kündigung), eine Bestellung ist ein einmaliger Vorgang. Anfrage, Angebot, Eingangs-, Bestell- und Zahlungsbestätigung hängen als **Dokumente** an der Bestellung. Rechnung und Lieferschein zeigen über **Gehört zu** auf sie und stehen dann unter *Verknüpfungen* der Bestellung. Die mitgelieferte Automatisierung **Rücksendefrist endet bald** erinnert 3 Tage vor dem Ende der Rücksendefrist (eingeschaltet; unter *Automatisierungen* abschaltbar).

**Beispiel:** Lena bestellt online einen Wasserkocher. Sie legt eine Bestellung an (Händler, Bestellnummer, Rücksendefrist bis) und hängt die Bestellbestätigung aus der E-Mail an. Kommt die Rechnung, wählt sie dort unter *Einzelheiten* bei „Gehört zu Vertrag / Bestellung“ die Bestellung – die Rechnung erscheint an der Bestellung, Bestätigung und Rechnung liegen zusammen.

Ansichten: *Rechnungen* mit *Offen*, *Dieses Jahr*, *Lieferscheine* und *Bestellungen* (darunter *Unterwegs*: bestellt, versandt oder teilweise angekommen).

## So rechnet das Paket

- **Status:** „offen – fällig am 15.11.2026“, „überfällig seit 01.11.2026“, „bezahlt am 09.11.2026“; bei Gutschriften „Gutschrift – noch nicht erhalten“ bzw. „Gutschrift erhalten am …“; bei Ausgangsrechnungen zählt der Zahlungseingang. Neu bei jeder Änderung und jeden Morgen über die mitgelieferte Automatisierung **„Rechnungen täglich prüfen“** (gleich eingeschaltet, änderbar unter Automatisierungen).
- **Positionen:** Ist der Gesamtpreis leer, füllt das Paket Menge × Einzelpreis ein – was du selbst einträgst, bleibt. Mit Umsatzsteuersatz gelten die Preise netto, das Paket rechnet die Umsatzsteuer aus.
- **Summenprüfung der Positionen:** Ergeben die Positionen (mit Umsatzsteuer) etwas anderes als der Betrag, steht an der Rechnung „Die Positionen ergeben 118,97 €, die Rechnung sagt 120,80 €.“ Bis 1 Cent je Position zählt als Rundung.
- **Steuerzeilen:** Je Satz eine Zeile – z. B. 0 %, 7 % und 19 % auf einer Rechnung. Ist der Steuerbetrag leer, rechnet das Paket Netto × Satz. *Netto gesamt* und *Umsatzsteuer gesamt* sind die Summen; passt Netto + Umsatzsteuer nicht zum Betrag, steht ein Hinweis an der Rechnung.
- **Steuerzeilen aus Positionen:** Haben Positionen einen Umsatzsteuersatz, legt das Paket je Satz eine Zeile „aus Positionen“ an und hält sie aktuell. Hat eine Rechnung eine Zeile von Hand, fasst es die Zeilen nicht an; änderst du eine Zeile „aus Positionen“, wird sie zu „von Hand“. Fällt ein Satz bei den Positionen weg, steht die Zeile auf 0 – löschen kannst du sie selbst.
- **Aus der E-Rechnung** füllt Ablago die Steuerzeilen noch nicht: Der Kern liest heute nur den Satz, wenn es genau einen gibt. Das kommt mit einer späteren Ablago-Version.
- Hinweise verschwinden, sobald es passt; Speichern hindern sie nie.

## Als bezahlt markieren

An der Rechnung trägt **Mappe → Als bezahlt markieren** *Bezahlt am* ein – heute oder ein Datum, das du wählst. Den Status rechnet das Paket danach neu. Ist die Rechnung schon bezahlt, steht das im Menü.

## Einstellungen

| Einstellung | Vorgabe | Bedeutung |
| --- | --- | --- |
| Positionen mit dem Betrag vergleichen | an | Aus: kein Hinweis zu den Positionen. |
| Steuerzeilen aus den Positionen füllen | an | Aus: Steuerzeilen nur von Hand. |

## Voraussetzungen

- Ablago ab 0.248.0 (Aktionen im Menü „Mappe“, Anzeige-Bedingungen, mehrere Ziele, berechnete Felder, Hinweise, Tabelle, „gehört immer zu“, eigene Organisation, Vorbelegen).
- Pakete Basis ab 1.7.0 und Verträge ab 1.0.0. Fahrzeuge, Haus, Vermietung, Haushalt und Kontierung sind nicht nötig – sind sie installiert, bieten *Betrifft*, *Steuerjahr*, *Kontierung* und *Steuerschlüssel* ihre Mappen an.

## Rechte und Netzwerkzugriff

- **Mappen lesen:** Rechnung, Rechnungsposition, Steuerzeile · **Mappen anlegen und ändern:** Rechnung (nur *Status*, *Netto gesamt*, *Umsatzsteuer gesamt*), Rechnungsposition (nur *Umsatzsteuer* und leere Gesamtpreise), Steuerzeile (leere Steuerbeträge; Zeilen „aus Positionen“ anlegen und aktuell halten; *Herkunft* auf „von Hand“, wenn du eine solche Zeile änderst).
- **Hinweise an Mappen setzen** (dms:hinweise) – nur an Rechnungen, nur zu den Summen.
- Keine Dokumente, **kein Zugriff auf Netzwerk und Internet**.
- Reagiert auf: `mappe.angelegt`, `mappe.geaendert` (Rechnungen, Positionen, Steuerzeilen), `zeitplan.ausgefuehrt` (Automatisierung „Rechnungen täglich prüfen“).

## Entwickeln

| Datei | Inhalt |
| --- | --- |
| [`code/rechnung.h`](code/rechnung.h) | Status, Positionen, Steuerzeilen, Summenprüfungen – ohne Ablago testbar |
| [`code/rechnungen.cpp`](code/rechnungen.cpp) | Ereignisse, Lesen und Schreiben über die API, Hinweise |
| [`tests/rechnung_test.cpp`](tests/rechnung_test.cpp) | läuft nativ in `code/bauen.sh` |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | das gebaute Modul gegen eine Nachbildung von Ablago |

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Rechnungen“ im Titel.
