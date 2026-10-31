# Haus

Das Paket **Haus** bringt die Mappentypen **Immobilie**, **Wartung** und **Zählerstand**. Damit weißt du, wann die Heizung gewartet werden muss, wer sie zuletzt gewartet hat und wie sich der Verbrauch entwickelt – im Eigenheim genauso wie als Mieter. Installiert wird es unter **Werkbank → Pakete**; die Pakete **Basis** und **Haushalt** kommen dabei automatisch mit.

![Die drei Mappentypen des Pakets mit ihren Feldern, Fristen und Beispielen](https://raw.githubusercontent.com/motom001/dms-registry/main/pakete/haus/bilder/ueberblick.png)

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Immobilie | Haus, Wohnung, Ferienwohnung, Garage, Grundstück | Bezeichnung (eindeutig), Art (Eigentum, Miete …), Anschrift, Baujahr, Wohnfläche, Grundstücksgröße, Eigentümer/Vermieter | – |
| Wartung | Heizung, Schornstein, Rauchmelder, Dach, Lüftung, Photovoltaik, Aufzug | Immobilie, Gegenstand, Fachbetrieb, Wartungsvertrag, zuletzt am, Turnus (Monate), Notiz | **Nächste fällig** (30 Tage vorher) |
| Zählerstand | eine Ablesung | Immobilie, Zählerart (Strom, Gas, Wasser, Wärme, Einspeisung), Zählernummer, abgelesen am, Stand, Einheit | – |

**Register:** Die **Immobilie** zeigt unter *Wartungen* und *Zählerstände* alle Mappen, die auf sie verweisen; dazu *Dokumente*, *Verknüpfungen* und *Historie*. Wartung und Zählerstand gehören zu ihrer Immobilie.

**Verweise:**

- **Eigentümer/Vermieter** und **Fachbetrieb** sind **Organisationen** aus dem Paket Basis.
- **Wartungsvertrag** ist ein **Vertrag** aus dem Paket Haushalt (Art z. B. „Sonstiges“).
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** des DMS – wo Grundbuchauszug, Kauf- oder Mietvertrag liegen.

**Fristen:** Trag nach jeder Wartung *Zuletzt am* und *Nächste fällig* ein („Zuletzt am“ plus Turnus). Das DMS erinnert 30 Tage vorher unter **Zu erledigen** und in der Ansicht **Anstehend**.

**Ansichten:** *Haus* mit allem und darunter *Immobilien*, *Wartungen*, *Zählerstände* (darunter *dieses Jahr* und *letztes Jahr* zum Vergleich) sowie *Wartung fällig* – Wartungen, die in den nächsten drei Monaten fällig oder schon überfällig sind.

**Beispiele (optional):** das Einfamilienhaus Musterweg 1 der Familie Muster mit Heizungs- und Rauchmelderwartung sowie je zwei Ablesungen von Strom- und Gaszähler. Wartungen und Zählerstände hängen schon am Haus; Fachbetrieb, Wartungsvertrag und Ablageort setzt du selbst.

## Voraussetzungen

- DMS ab Version 0.79 (Verweis auf den Ablageort des DMS, Verweise zwischen Beispielen)
- Pakete **Basis** ab 1.0.0 und **Haushalt** ab 1.0.0 – werden bei der Installation aus dem Katalog mitinstalliert

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. Die eigene **Immobilie** anlegen.
2. Fachbetriebe (Heizungsbauer, Schornsteinfeger) als **Organisation** anlegen.
3. Je Wartung eine Mappe **Wartung** mit *Nächste fällig* anlegen; Rechnungen und Prüfprotokolle als Dokumente dazulegen.
4. Zählerstände beim Ablesen eintragen – am besten mit einem Foto des Zählers als Dokument.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Haus“ im Titel.
