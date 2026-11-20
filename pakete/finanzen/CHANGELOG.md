# Änderungen

## 1.2.0

- Ansichten mit Symbolen. Ein Update nimmt keine Ansichten weg: In bestehenden Ablagen bleiben weggefallene Ansichten stehen, bis du sie löschst (Thomas, 20.11.2026).

## 1.1.0

- **Tipps auf Englisch** (Ablago #1307, dms-registry #202): Die Texte der drei Tipps stehen jetzt in `texte/de/entdecken.json` und `texte/en/entdecken.json`. Ablago zeigt sie in der Sprache der Person. Braucht **Ablago 0.293.2**.

## 1.0.0

- Erste Fassung (dms-registry #212): **Konto** und **Steuerjahr** aus dem Paket Haushalt, dazu **Kontoauszug** und **Freistellungsauftrag**.
  - Konto: Titel „{Bank} von {Inhaber} ({Art})“; Register „Kontoauszüge“ und „Was läuft über dieses Konto?“.
  - Steuerjahr: bei „beruflich genutzt“ ein Abschnitt mit Umsatzsteuer, Gewerbesteuer und Jahresabschluss; „Belege“ zeigt alles, was auf das Jahr zeigt.
  - Automatisierung „Einspruchsfrist beim Steuerbescheid“ und zwei Tipps aus Haushalt.
- Braucht **Ablago 0.285.0** und **Basis 1.7.0**. Ein Umzug aus Haushalt 2.x ist nicht vorgesehen.
