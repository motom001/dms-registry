# Änderungen

## 1.2.0

- Neu: **vorgefertigte Automatisierungen** für jede Frist (1). Seit Ablago 0.177.0 erinnert ein Datumsfeld nicht mehr selbst – die Automatisierung „Datum erreicht“ tut es, Vorlaufzeit, Empfänger und Text stellst du selbst ein. Beim Installieren fragt Ablago, welche gleich eingeschaltet werden (Vorgabe: alle); bei einem Update ersetzt die mitgelieferte die übernommene Erinnerung, solange du sie nicht geändert hast.
- Braucht Ablago ab 0.177.0.

## 1.1.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.1.0

- **Formate** (dms-registry #55, DMS #535): Neues Feld **Land** an der Immobilie (Vorgabe Deutschland). Die PLZ hat in Deutschland genau 5 Ziffern, bei einem anderen Land ist sie frei.
- **Zuletzt am** (Wartung) und **Abgelesen am** (Zählerstand) dürfen nicht in der Zukunft liegen.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update ergänzt das Feld Land und übernimmt Formate und Grenzen nur an Feldern, an denen du nichts davon eingestellt hast.

## 1.0.2

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.0.1

- Beispiele zeigen jetzt auf die Immobilie: Wartungen und Zählerstände hängen am Einfamilienhaus Musterweg 1.
- Braucht DMS ab 0.79.0 (Verweise zwischen Beispielen).

## 1.0.0

- Erste Fassung.
