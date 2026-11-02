# Änderungen

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
