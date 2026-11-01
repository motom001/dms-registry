# Fahrplan (Roadmap)

Wie wir entscheiden, welche Pakete als Nächstes in den Katalog kommen – und wo du den aktuellen Stand siehst.

**Der aktuelle Fahrplan steht in den [Meilensteinen](https://github.com/motom001/dms-registry/milestones?direction=asc&sort=title&state=open).** Was das DMS selbst dafür braucht (zum Beispiel den Paket-Läufer für Pakete mit Code), steht in den [Meilensteinen von motom001/dms](https://github.com/motom001/dms/milestones?direction=asc&sort=title&state=open) – beide nutzen dieselben Nummern. Diese Seite erklärt nur, wie man sie liest; sie wird nicht bei jeder Änderung angepasst.

## Pakete statt Einzelstücke

Zusammengehörige Wünsche werden zu einem **Paket** im Fahrplan gebündelt – zum Beispiel mehrere Verarbeitungs-Pakete, die alle den Paket-Läufer brauchen. Jedes solche Bündel ist ein **Meilenstein** auf GitHub. Dort steht in wenigen Sätzen, was du davon hast, welche Issues dazugehören und wie weit es ist (Fortschrittsbalken).

## So liest du die Meilensteine

- **Nummer vorn = Reihenfolge.** `02 · …` kommt vor `07 · …`. Was weiter hinten steht, ist geplant, aber nicht versprochen.
- **„Später“** sammelt gute Ideen ohne festen Platz in der Reihenfolge.
- **„Zurückgestellt“** sammelt, was bewusst geparkt ist. Die Begründung steht im jeweiligen Issue.
- **Geschlossene Meilensteine** sind erledigt; welche Version eines Pakets was enthält, steht im `CHANGELOG.md` des Pakets.

## Ein Bündel nach dem anderen

- In den Katalog kommt nur, was der Maintainer mit dem Label **`freigegeben`** versieht – in der Regel die Issues des aktuellen Meilensteins.
- Das nächste Bündel ist schon beschrieben und sortiert, wird aber erst freigegeben, wenn das aktuelle fertig ist. So bauen spätere Pakete auf dem auf, was das DMS dann wirklich kann.
- Korrekturen an bestehenden Paketen (neue Patch-Version) gehen jederzeit dazwischen.

## Wünsche und eigene Pakete einbringen

Wünsche und eigene Pakete sind willkommen – als [Issue](https://github.com/motom001/dms-registry/issues/new) im Format einer User Story mit Akzeptanzkriterien. Neue Wünsche werden bewertet und einem Meilenstein zugeordnet, unter „Später“ einsortiert oder bewusst zurückgestellt. Wie ein Beitrag abläuft (Vorlage, Prüfung, `Signed-off-by`), steht in [CONTRIBUTING.md](CONTRIBUTING.md), die Regeln für Pakete in [REGELN.md](REGELN.md).
