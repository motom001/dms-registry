# Sicherheit

**Deutsch** · [English](SECURITY.en.md)

Dieses Repository gehört zum DMS ([motom001/dms](https://github.com/motom001/dms)) und enthält: Pakete, Katalog und Prüfwerkzeuge.

## Eine Sicherheitslücke melden

Bitte **kein öffentliches Issue** für Sicherheitslücken. Melde sie vertraulich über GitHub: **Security → Report a vulnerability** in diesem Repository ([Private Vulnerability Reporting](https://github.com/motom001/dms-registry/security/advisories/new)).

Betrifft die Lücke das DMS selbst, melde sie bitte direkt im Repository [motom001/dms](https://github.com/motom001/dms/security/advisories/new).

## Was automatisch geprüft wird

| Was | Womit | Wann |
| --- | --- | --- |
| Prüfwerkzeuge (Python), Workflows | CodeQL | jeder Pull Request, jeder Push auf `main` |
| Pakete im Katalog | `pruefen.py` (Schema, Regeln, Signed-off-by) | jeder Pull Request |
| GitHub-Actions | Dependabot (Warnungen und Updates) | jeder Pull Request, wöchentlich |
| Geheimnisse (Tokens, Passwörter) | Secret Scanning mit Push-Schutz | jeder Push |

Die Funde stehen unter **Security** in diesem Repository.

Meldungen auf Deutsch oder Englisch sind willkommen. Bei Abweichungen zwischen deutscher und englischer Fassung gilt die deutsche.
