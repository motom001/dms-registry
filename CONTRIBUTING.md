# Ein Paket beitragen

1. **Issue anlegen** – als User Story: „Als … möchte ich ein Paket …, damit …“, mit Akzeptanzkriterien. Bei einer Änderung an einem bestehenden Paket nenne das Paket.
2. **Freigabe abwarten.** Aufgenommen wird nur, was das Label `freigegeben` trägt; das vergibt allein der Maintainer.
3. **Forken, Paket anlegen:** `werkzeuge/neues-paket.sh <id> "<Name>"` kopiert die Vorlage nach `pakete/<id>/`.
4. **Ausfüllen:** `manifest.yaml`, `README.md`, `LICENSE` (Jahr und Name), `CHANGELOG.md`, Inhalte unter `inhalt/`, Erwartungen unter `tests/`. Beispiele stehen als Kommentare in der Vorlage.
5. **Prüfen:** `python3 werkzeuge/pruefen.py pakete/<id>` (braucht `pip install pyyaml jsonschema`). Dieselbe Prüfung läuft im Pull Request.
6. **Pull Request** mit `Closes #…`. Jeder Commit trägt ein `Signed-off-by:` (`git commit -s`). Damit bestätigst du nach dem [Developer Certificate of Origin](https://developercertificate.org/), dass du den Beitrag unter der Lizenz des Pakets einbringen darfst.
7. **Pflege:** Trage dich in `.github/CODEOWNERS` für dein Paket ein. Du kümmerst dich um Fehler und neue DMS-Versionen; der Maintainer gibt frei und mergt.

Fragen gern im Issue. Wie die Arbeit am DMS selbst läuft, steht im [Entwicklerhandbuch](https://motom001.github.io/dms/entwickler/aktuell/).

Für den Umgang miteinander gilt unser [Verhaltenskodex](CODE_OF_CONDUCT.md).
