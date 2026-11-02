# Änderungen

## 1.1.0

- **Formate** (dms-registry #55, DMS #535): Neues Feld **Land** am Mietobjekt (Vorgabe Deutschland). Die PLZ hat in Deutschland genau 5 Ziffern, bei einem anderen Land ist sie frei.
- **Gekündigt am**, **Kaution zurückgezahlt am** (Mietvertrag) und **Versendet am** (Nebenkostenabrechnung) dürfen nicht in der Zukunft liegen.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update ergänzt das Feld Land und übernimmt Formate und Grenzen nur an Feldern, an denen du nichts davon eingestellt hast.

## 1.0.2

- **Erkennung** (dms-registry #49, DMS #336/#391): „für die Erkennung“ markiert – das **Aktenzeichen Grundsteuer** am Mietobjekt (Post mit diesem Aktenzeichen gehört zum Mietobjekt) sowie **Rechnungsdatum**, **Betrag** und **Firma** einer Ausgabe („Aus Dokument ausfüllen“ nimmt sie aus der Rechnung).
- Braucht DMS ab 0.113.0. Inhalt sonst unverändert; das Update übernimmt die Markierung nur an Feldern, an denen du nichts zur Erkennung eingestellt hast.

## 1.0.1

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.0.0

- Erste Fassung: Mietobjekt, Wohnung, Mietvertrag, Nebenkostenabrechnung und Ausgabe Mietobjekt mit Fristen und Ansichten.
