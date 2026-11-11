# Änderungen

## 2.0.0

- **Breaking Change – Mietvertrag und Ausgabe ziehen in die Pakete Verträge und Rechnungen** (dms-registry #163): Vermietung bringt die Mappentypen *Mietvertrag* und *Ausgabe Mietobjekt* nicht mehr mit.
  - Ein Mietverhältnis ist ein **Vertrag** aus dem Paket Verträge mit der Vertragsart *Miete*: *Betrifft* = die Wohnung, *Kunde* = die Mieter; Miete und Kaution stehen im Abschnitt *Miete*. Das Paket Verträge rechnet Status, Kündigungsfrist und Ende aus.
  - Eine Ausgabe ist eine **Rechnung** aus dem Paket Rechnungen mit *Betrifft* = Mietobjekt oder Wohnung; *Umlagefähig* und *Kostenart* stehen im Abschnitt *Vermietung*.
  - Bestehende Mappen ziehen beim Installieren bzw. Aktualisieren von **Verträge 1.1.0** und **Rechnungen 1.1.0** dorthin um, mit allen Werten und Dokumenten (Ablago 0.243.0, „Umbau“). Deshalb erst Verträge, dann Rechnungen, dann dieses Update.
- Registers *Mietverträge* (Wohnung) und *Ausgaben* (Mietobjekt, Wohnung) zeigen Verträge bzw. Rechnungen, deren *Betrifft* hierher zeigt. Neu an der **Nebenkostenabrechnung:** *Rechnungen* – die umgelegten Rechnungen des Jahres.
- Ansichten *Mietverträge*, *Ausgaben* (mit *dieses Jahr*, *letztes Jahr*, *Umlagefähig letztes Jahr*), *Mieterhöhung möglich* und *Vertrag endet bald* zeigen jetzt Verträge bzw. Rechnungen. *Laufende Mietverträge* entfällt (das Paket Verträge hat *Gekündigt*), ebenso die Automatisierung „Mietvertrag endet bald“ (Verträge erinnert an *Kündigen bis*). „Mieterhöhung möglich“ bleibt und gilt für Verträge.
- In einer bestehenden Ablage bleiben die alten Ansichten erhalten und zeigen nach dem Umzug auf Verträge bzw. Rechnungen – und zwar auf **alle** (*Vermietung*, *Mietverträge*, *Ausgaben*); setz dort die Bedingung „Betrifft zeigt auf eine Mappe vom Typ Wohnung“ bzw. „… Mietobjekt oder Wohnung“. Die Bedingung „Stand läuft oder gekündigt“ (*Laufende Mietverträge*, *Mieterhöhung möglich*) passt danach nicht mehr – der Stand steht in der Notiz; bitte die Ansicht anpassen oder löschen.
- Haushalt ist keine Abhängigkeit mehr: Das Steuerjahr an der Nebenkostenabrechnung zeigt auf ein Steuerjahr aus Haushalt, wenn Haushalt installiert ist. Kurzanleitung „So nutzt du es“ (dms-registry #164).
- Hängt jetzt ab von **Basis 1.7.0, Haus, Verträge 1.1.0 und Rechnungen 1.1.0**; braucht Ablago 0.243.0.

## 1.4.1

- Das Feld **Verbleib Originaldokumente** verweist auf den Ablageort aus dem Paket **Basis** (`basis:ablageort` statt `dms:ablageort`, dms-registry #138, Ablago #883). Braucht Basis ab 1.6.0 und Ablago ab 0.212.0. In einer bestehenden Ablage ändert sich nichts: Basis übernimmt den bisherigen Ablageort mit allen Orten, das Feld zeigt weiter darauf.

## 1.4.0

- Neu: **englische Beschriftungen** für Mappentypen, Felder, Auswahlwerte, Register und Ansichten (`beschriftungen.en`, Registry #116 und #135). Ablago ab 0.200.0 zeigt sie, wenn jemand Englisch gewählt hat; ein Update ergänzt sie an installierten Mappentypen, ohne eigene Beschriftungen zu überschreiben. Ältere Ablago-Versionen übergehen sie – dafür braucht es kein höheres `dms`. Gespeicherte Werte ändern sich nicht.

## 1.3.0

- Neu: **vorgefertigte Automatisierungen** für jede Frist (3). Seit Ablago 0.177.0 erinnert ein Datumsfeld nicht mehr selbst – die Automatisierung „Datum erreicht“ tut es, Vorlaufzeit, Empfänger und Text stellst du selbst ein. Beim Installieren fragt Ablago, welche gleich eingeschaltet werden (Vorgabe: alle); bei einem Update ersetzt die mitgelieferte die übernommene Erinnerung, solange du sie nicht geändert hast.
- Braucht Ablago ab 0.177.0.

## 1.2.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.2.0

- Neu: **gleichbedeutende Wörter** für die Suche – wer „Nebenkosten“ sucht, findet auch „Betriebskosten“; dazu Abrechnung, Kaltmiete, Kaution und Mieter.
- Braucht DMS ab 0.127.0 (Wortlisten).

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
