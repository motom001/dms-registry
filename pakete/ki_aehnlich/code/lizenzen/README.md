# Fremdes im Paket

Das Modul (`code/aehnlich.cpp`) ist eigener Code unter Apache-2.0. Die Daten in `code/daten/` entstehen beim Bau
(`code/bauen.sh`, `code/umwandeln.py`) aus einem fremden Modell, festgelegt auf einen Commit:

| Was | Herkunft | Lizenz |
| --- | --- | --- |
| Token-Vektoren (`modell.dat`) | [sentence-transformers/static-similarity-mrl-multilingual-v1](https://huggingface.co/sentence-transformers/static-similarity-mrl-multilingual-v1), Datei `0_StaticEmbedding/model.safetensors` – davon die ersten 256 von 1024 Dimensionen, auf 8 Bit gerundet | Apache-2.0 |
| Vokabular (`vokabular.txt`) | Tokenizer desselben Modells (`0_StaticEmbedding/tokenizer.json`), das Vokabular von [bert-base-multilingual-uncased](https://huggingface.co/google-bert/bert-base-multilingual-uncased) | Apache-2.0 |
| Zeichentabellen (`zeichen.dat`) | aus der Unicode-Datenbank von Python (`unicodedata`) | [Unicode License v3](https://www.unicode.org/license.txt) |

Der Text der Apache-Lizenz steht in `../../LICENSE`. Das Modell hat keine Nutzungsbeschränkungen über die
Apache-Lizenz hinaus.
