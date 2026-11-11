# Änderungen

## 2.0.0

- **Breaking Change – Vertrag und Versicherung ziehen ins Paket Verträge** (dms-registry #163): Haushalt bringt die Mappentypen *Vertrag* und *Versicherung* nicht mehr mit. Verträge und Versicherungen legst du als **Vertrag** aus dem Paket Verträge an (Versicherung ist dort eine Vertragsart); es rechnet *Kündigen bis* selbst aus. Bestehende Mappen ziehen beim Installieren bzw. Aktualisieren von **Verträge 1.1.0** dorthin um – mit allen Werten, Dokumenten, Verknüpfungen, Ansichten und Rechten (Ablago 0.243.0, „Umbau“). Deshalb erst Verträge, dann Rechnungen, dann dieses Update.
- Neu an der **Anschaffung:** Register *Rechnungen* – Kassenbon und Rechnung sind Rechnungen aus dem Paket Rechnungen mit *Betrifft* = diese Anschaffung. Am **Steuerjahr** erscheinen unter *Belege* auch Rechnungen mit diesem Steuerjahr.
- Ansichten *Verträge*, *Versicherungen* (Verträge mit ausgefüllter Versicherung), *Sach-* und *Personenversicherungen* und *Kündigung in den nächsten 3 Monaten* zeigen jetzt Verträge aus dem Paket Verträge. Die Automatisierungen „Kündigung … bald fällig“ entfallen (das Paket Verträge bringt „Vertrag rechtzeitig kündigen“ mit); „Hauptfälligkeit einer Versicherung“ bleibt und gilt für Verträge.
- In einer bestehenden Ablage bleiben die bisherigen Ansichten, wie sie sind; nach dem Umzug zeigen *Verträge* und *Versicherungen* dort **alle** Verträge (auch Mietverträge). Am einfachsten setzt du bei *Versicherungen* die Bedingung „Versicherung ist nicht leer“.
- Die Beispiel-Verträge und -Versicherungen entfallen (Beispiele bringt das Paket Verträge mit).
- Hängt jetzt ab von **Basis 1.7.0, Verträge 1.1.0 und Rechnungen 1.1.0**; braucht Ablago 0.243.0.

## 1.4.1

- Das Feld **Verbleib Originaldokumente** verweist auf den Ablageort aus dem Paket **Basis** (`basis:ablageort` statt `dms:ablageort`, dms-registry #138, Ablago #883). Braucht Basis ab 1.6.0 und Ablago ab 0.212.0. In einer bestehenden Ablage ändert sich nichts: Basis übernimmt den bisherigen Ablageort mit allen Orten, das Feld zeigt weiter darauf.

## 1.4.0

- Neu: **englische Beschriftungen** für Mappentypen, Felder, Auswahlwerte, Register und Ansichten (`beschriftungen.en`, Registry #116 und #135). Ablago ab 0.200.0 zeigt sie, wenn jemand Englisch gewählt hat; ein Update ergänzt sie an installierten Mappentypen, ohne eigene Beschriftungen zu überschreiben. Ältere Ablago-Versionen übergehen sie – dafür braucht es kein höheres `dms`. Gespeicherte Werte ändern sich nicht.

## 1.3.0

- Neu: **vorgefertigte Automatisierungen** für jede Frist (6). Seit Ablago 0.177.0 erinnert ein Datumsfeld nicht mehr selbst – die Automatisierung „Datum erreicht“ tut es, Vorlaufzeit, Empfänger und Text stellst du selbst ein. Beim Installieren fragt Ablago, welche gleich eingeschaltet werden (Vorgabe: alle); bei einem Update ersetzt die mitgelieferte die übernommene Erinnerung, solange du sie nicht geändert hast.
- Braucht Ablago ab 0.177.0.

## 1.2.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.2.0

- **Formate** (dms-registry #55, DMS #535): Die **IBAN** eines Kontos prüft das DMS mit Länge und Prüfziffer und zeigt sie in Vierergruppen. Der Ausweis bleibt bei „Gültig bis“ ohne Grenze – das Datum liegt ja meist in der Zukunft.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update übernimmt das Format nur, wenn du am Feld nichts davon eingestellt hast.

## 1.1.0

- **Personen als Verweis** (dms-registry #52, DMS #534): Wo ein Mensch gemeint ist, steht jetzt ein Verweis auf eine **Person** aus dem Paket Basis statt Text – **Konto → Inhaber** (mehrere, z. B. Gemeinschaftskonto), **Versicherung → Versichert** (mehrere), **Arbeitsverhältnis, Vorsorge, Ausweis & Urkunde, Gesundheit, Bildung → Person**. Verweisart Bezug: Wer eine Person löscht, löscht damit nicht Konto oder Vertrag. An der Person siehst du unter *Verknüpfungen* alles, was zu ihr gehört.
  - Titel und Trefferlisten zeigen den Namen der verwiesenen Person. Sachen (z. B. das Auto) verweisen selbst auf ihre Versicherung und stehen dort unter *Verknüpfungen*.
  - **Update:** Die bisherigen Textfelder bleiben mit allen Werten; die Verweisfelder kommen dazu. Unter **Werkbank → Pakete → Haushalt → Text in Verweise umwandeln** schlägt das DMS je Name eine vorhandene Person vor oder legt eine neue an („Lena und Tom Muster“ wird zu zwei Personen) – erst nach deiner Vorschau, rückgängig zu machen. Updates ändern nichts heimlich.
  - Die Verweisfelder sind keine Pflicht (auch wo „Person“ als Text Pflicht war), damit vorhandene Mappen nach dem Update passen.
- **Beispiele:** Familie Muster heißt jetzt Lena, Tom und Jonas und ist als drei **Personen** dabei; Konten, Versicherungen, Arbeitsverhältnis, Vorsorge, Ausweis, Gesundheit und Bildung verweisen auf sie (18 Beispiele).
- Braucht DMS ab 0.120.0 und Basis ab 1.1.0 (Person).

## 1.0.3

- **Erkennung** (dms-registry #49, DMS #336/#391): **Vertragsnummer** (Vertrag, Vorsorge) und **Versicherungsnummer** sind „für die Erkennung“ markiert – Post mit dieser Nummer wird dem Vertrag bzw. der Versicherung vorgeschlagen und kann, wenn du es am Mappentyp einschaltest, automatisch zugeordnet werden.
- Die IBAN eines Kontos bleibt bewusst unmarkiert: Sie steht in fast jedem Lastschrift-Brief und würde dann jede Rechnung dem Konto zuordnen.
- Braucht DMS ab 0.113.0. Das Update übernimmt die Markierung nur an Feldern, an denen du nichts zur Erkennung eingestellt hast.

## 1.0.2

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.0.1

- Beispiele zeigen jetzt aufeinander und auf Basis: Girokonto → Sparkasse, Strom → Stadtwerke, Impfung → Praxis Dr. Beispiel, Arbeitsverhältnis → Steuerjahr 2025. Neues Beispiel Kfz-Versicherung (für das Paket Fahrzeuge).
- Braucht DMS ab 0.79.0 (Verweise zwischen Beispielen).

## 1.0.0

- Erste Fassung.
