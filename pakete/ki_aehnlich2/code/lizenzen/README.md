# Fremdes im Paket

Das Modul (`code/e5.cpp`) ist eigener Code unter Apache-2.0. Die Daten in `code/daten/` entstehen beim Bau
(`code/bauen.sh`, `code/umwandeln.py`) aus einem fremden Modell, festgelegt auf einen Commit:

| Was | Herkunft | Lizenz |
| --- | --- | --- |
| Gewichte (`modell.dat`), auf 8 Bit gerundet, Wortteile gekürzt | [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small), Commit `614241f6` | MIT (`MIT.txt`) |
| Wortteile und Normalisierung (`vokabular.dat`, `normal.dat`) | Tokenizer desselben Modells (`tokenizer.json`), SentencePiece von [XLM-RoBERTa](https://huggingface.co/FacebookAI/xlm-roberta-base) | MIT (`MIT.txt`) |

Der Text der Apache-Lizenz steht in `../../LICENSE`. Das Modell hat keine Nutzungsbeschränkungen über die
MIT-Lizenz hinaus. Veröffentlichung zum Modell: Wang et al., „Multilingual E5 Text Embeddings: A Technical
Report“, 2024.
