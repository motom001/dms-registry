# Änderungen

## 2.0.1

- Vorlage *Kaufvertrag Gebrauchtwagen*: Ablagos Briefsatz kennt keine Tabellen und keine Kästchen-Zeichen – die Fahrzeugdaten stehen jetzt Zeile für Zeile, Ankreuzfelder als „[ ]“, Lücken als Punkte.

## 2.0.0

- **Breaking Change – Werkstattrechnung zieht ins Paket Rechnungen** (dms-registry #163): Fahrzeuge bringt den Mappentyp *Werkstattrechnung* nicht mehr mit. Rechnungen zum Fahrzeug legst du als **Rechnung** aus dem Paket Rechnungen ab und wählst unter *Betrifft* das Fahrzeug; Kilometerstand und Arbeiten stehen dort im Abschnitt *Fahrzeug*. Bestehende Werkstattrechnungen ziehen beim Installieren bzw. Aktualisieren von **Rechnungen 1.1.0** dorthin um, mit allen Werten und Dokumenten (Ablago 0.243.0, „Umbau“). Deshalb erst Verträge, dann Rechnungen, dann dieses Update.
- **Versicherung** und **Finanzierung/Leasing** am Fahrzeug zeigen auf einen **Vertrag** aus dem Paket Verträge (bisher Versicherung bzw. Vertrag aus Haushalt). In einer bestehenden Ablage zeigen die Felder nach dem Umzug durch Verträge 1.1.0 von selbst dorthin.
- Das Register am Fahrzeug heißt jetzt *Rechnungen* und zeigt alle Rechnungen mit *Betrifft* = dieses Fahrzeug (in einer bestehenden Ablage behält es seinen Namen). Die Ansicht *Werkstattrechnungen* heißt *Rechnungen zu Fahrzeugen*.
- In einer bestehenden Ablage bleiben die bisherigen Ansichten; nach dem Umzug zeigen *Fahrzeuge* und *Werkstattrechnungen* dort **alle** Rechnungen. Setz bei *Werkstattrechnungen* die Bedingung „Betrifft zeigt auf eine Mappe vom Typ Fahrzeug“ und nimm die Rechnung aus *Fahrzeuge* heraus.
- Neu: Vertragsarten **Pkw-Kaufvertrag** (mit einer schlichten Vorlage „Kaufvertrag Gebrauchtwagen“, die Fahrzeugdaten, Käufer, Verkäufer und Preis aus dem Vertrag einsetzt) und **Leasing** für das Paket Verträge.
- Beispiele: die Kfz-Versicherung ist jetzt ein Vertrag, die zwei Werkstattrechnungen sind Rechnungen. Der Halter „Tom“ entfällt (Haushalt ist keine Abhängigkeit mehr).
- Kurzanleitung „So nutzt du es“ (dms-registry #164).
- Hängt jetzt ab von **Basis 1.7.0, Verträge 1.1.0 und Rechnungen 1.1.0** statt Haushalt; braucht Ablago 0.243.0.

## 1.5.1

- Das Feld **Verbleib Originaldokumente** verweist auf den Ablageort aus dem Paket **Basis** (`basis:ablageort` statt `dms:ablageort`, dms-registry #138, Ablago #883). Braucht Basis ab 1.6.0 und Ablago ab 0.212.0. In einer bestehenden Ablage ändert sich nichts: Basis übernimmt den bisherigen Ablageort mit allen Orten, das Feld zeigt weiter darauf.

## 1.5.0

- Neu: **englische Beschriftungen** für Mappentypen, Felder, Auswahlwerte, Register und Ansichten (`beschriftungen.en`, Registry #116 und #135). Ablago ab 0.200.0 zeigt sie, wenn jemand Englisch gewählt hat; ein Update ergänzt sie an installierten Mappentypen, ohne eigene Beschriftungen zu überschreiben. Ältere Ablago-Versionen übergehen sie – dafür braucht es kein höheres `dms`. Gespeicherte Werte ändern sich nicht.

## 1.4.0

- Neu: **vorgefertigte Automatisierungen** für jede Frist (1). Seit Ablago 0.177.0 erinnert ein Datumsfeld nicht mehr selbst – die Automatisierung „Datum erreicht“ tut es, Vorlaufzeit, Empfänger und Text stellst du selbst ein. Beim Installieren fragt Ablago, welche gleich eingeschaltet werden (Vorgabe: alle); bei einem Update ersetzt die mitgelieferte die übernommene Erinnerung, solange du sie nicht geändert hast.
- Neu am Fahrzeug: Feld **Verantwortlich** (Verweis auf einen Benutzer) – an ihn geht die HU-Erinnerung. Der Halter bleibt eine Person und kann jemand ohne Konto sein.
- Braucht Ablago ab 0.177.0.

## 1.3.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.3.0

- Neu: **gleichbedeutende Wörter** für die Suche – wer „Kfz“ sucht, findet auch „Auto“ und „PKW“; dazu HU/TÜV, Fahrzeugbrief und Fahrzeugschein mit ihren amtlichen Namen, Werkstatt- und Reparaturrechnung.
- Braucht DMS ab 0.127.0 (Wortlisten).

## 1.2.0

- **Grenzen** (dms-registry #55, DMS #535): Die **Erstzulassung** darf nicht in der Zukunft liegen. „HU fällig“ bleibt ohne Grenze.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update übernimmt die Grenze nur, wenn du am Feld nichts davon eingestellt hast.

## 1.1.0

- **Halter als Verweis auf eine Person** (dms-registry #52, DMS #534): Am Fahrzeug ist der **Halter** jetzt ein Verweis auf eine **Person** aus dem Paket Basis (Verweisart Bezug: Wer eine Person löscht, löscht damit nicht das Auto). An der Person siehst du unter *Verknüpfungen* ihre Fahrzeuge.
  - **Update:** Das bisherige Textfeld *Halter* bleibt mit allen Werten; das Verweisfeld kommt dazu. Unter **Werkbank → Pakete → Fahrzeuge → Text in Verweise umwandeln** schlägt das DMS je Name eine vorhandene Person vor oder legt eine neue an – erst nach deiner Vorschau, rückgängig zu machen. Updates ändern nichts heimlich.
  - Das Beispiel-Familienauto verweist auf Tom Muster aus den Beispielen von Haushalt.
- Braucht DMS ab 0.120.0, Basis ab 1.1.0 (Person) und Haushalt ab 1.1.0.

## 1.0.3

- **Erkennung** (dms-registry #49, DMS #336/#391): **Kennzeichen** und **Fahrzeug-Identnummer** sind „für die Erkennung“ markiert – Post mit einer davon (Kfz-Steuer, Versicherung, Werkstatt) gehört zu diesem Fahrzeug. Bei der Werkstattrechnung füllt „Aus Dokument ausfüllen“ Werkstatt, Datum und Betrag.
- Behoben: Der Hilfetext der Fahrzeug-Identnummer war nach „ohne I“ abgeschnitten (Komma in YAML ohne Anführungszeichen); er gilt für Neuinstallationen.
- Braucht DMS ab 0.113.0. Das Update übernimmt die Markierung nur an Feldern, an denen du nichts zur Erkennung eingestellt hast.

## 1.0.2

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.0.1

- Beispiele zeigen jetzt aufeinander: Werkstattrechnungen → Familienauto, Familienauto → Kfz-Versicherung aus Haushalt.
- Braucht DMS ab 0.79.0 (Verweise zwischen Beispielen).

## 1.0.0

- Erste Fassung.
