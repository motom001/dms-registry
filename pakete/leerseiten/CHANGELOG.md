# Änderungen

## 1.0.0

- Erste Fassung (dms #997): erkennt leere Seiten in neuer Post (PDF, JPEG, PNG) und markiert sie über die Schnittstelle `dms:leerseiten` von Ablago 0.255.0. Das Paket löscht nichts; die Seiten fallen erst weg, wenn eine Person die Post in eine Mappe übernimmt.
- Erkennung ohne fremde Bibliotheken (`gemeinsam/leerseite/`, auch im Paket Trennblatt): Papierton, Tinte je nach Empfindlichkeit, Staub, Lochung und Schatten am Rand zählen nicht.
- Einstellungen: Empfindlichkeit (vorsichtig, normal, streng; Vorgabe vorsichtig), Kanäle (Vorgabe Scan, Eingangsordner, Hochgeladen), höchstens so viele Seiten.
- Tests mit künstlichen Scans: leer, Lochung und Schatten, Bleistiftnotiz, Stempel, durchscheinende Schrift, Staub.
