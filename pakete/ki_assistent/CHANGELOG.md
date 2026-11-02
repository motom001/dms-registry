# Änderungen

## 1.1.0

- Neu: **Aus Dokument ausfüllen** über den KI-Dienst (dms-registry #64, DMS #511). Das Paket beantragt dafür zusätzlich das Recht **„Felder aus Dokumenten vorschlagen“ (`dms:erkennen`)** – das DMS zeigt es beim Update und lässt es bestätigen. Es bekommt nur den Text des Dokuments und die Beschreibung der Felder als JSON Schema.
- Strukturierte Ausgabe: Anfrage mit `response_format` vom Typ `json_schema` (Ollama ab 0.5, llama.cpp-Server, LocalAI, vLLM); kennt der Dienst das nicht, ein zweiter Versuch mit „nur JSON“. Der Text geht abgegrenzt als Daten an den Dienst, getrennt von der Aufgabe.
- Das Paket prüft die Antwort, bevor es sie weitergibt: unbekannte Felder und Werte, die nicht zum Schema passen, fallen weg. Ist nichts Brauchbares dabei, antwortet der Dienst nicht oder nicht rechtzeitig, meldet das Paket einen Fehler – das DMS nimmt dann die eingebaute Erkennung.
- Neue Einstellungen im Abschnitt *Aus Dokument ausfüllen*: **Für „Aus Dokument ausfüllen“ nutzen** (Standard an) und **Zeitgrenze** (Standard 50 Sekunden).
- Braucht DMS ab 0.125.0. „Frag deine Ablage“ bleibt unverändert.

## 1.0.0

- Erste Fassung: beantwortet Fragen an die Ablage („Frag deine Ablage“, DMS 0.124.0) über einen Dienst mit OpenAI-kompatibler Schnittstelle (Chat Completions, Antwort Stück für Stück), Netz nur zur bestätigten Dienst-Adresse, „Verbindung testen“ mit Modellliste und Antwortzeit.
