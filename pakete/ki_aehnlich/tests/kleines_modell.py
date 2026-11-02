#!/usr/bin/env python3
"""
Kleines Modell im Format von static-similarity-mrl-multilingual-v1 – für die Tests ohne Netz.

    python3 kleines_modell.py <zielordner>

Schreibt tokenizer.json (wie das echte: BertNormalizer, BertPreTokenizer, WordPiece) und model.safetensors.
Jedes Token hat einen eigenen Einheitsvektor (Token i → Dimension i), so verrät der Vektor eines Textes,
welche Tokens wie oft darin vorkommen. Die Tabelle hat 40 Spalten; umgewandelt werden die ersten 32.
"""
import json, struct, sys
from pathlib import Path

TOKENS = ['[PAD]', '[UNK]', '[CLS]', '[SEP]', 'rechnung', 'heizung', 'gas', '##therme', 'wartung', 'der', 'fur', 'die',
          'prufung', ',', '!', '.', '中', '文', 'strom', '##es', 'kundigung', 'handy', '##vertrag', 'vertrag', 'ı',
          '-', 'e', '##e', 'œ', 'u', 'ß', 'grosse']
SPALTEN = 40


def main():
    ziel = Path(sys.argv[1])
    ziel.mkdir(parents=True, exist_ok=True)
    tok = {
        'version': '1.0', 'truncation': None, 'padding': None, 'added_tokens': [],
        'normalizer': {'type': 'BertNormalizer', 'clean_text': True, 'handle_chinese_chars': True, 'strip_accents': None, 'lowercase': True},
        'pre_tokenizer': {'type': 'BertPreTokenizer'},
        'model': {'type': 'WordPiece', 'unk_token': '[UNK]', 'continuing_subword_prefix': '##', 'max_input_chars_per_word': 100,
                  'vocab': {t: i for i, t in enumerate(TOKENS)}},
    }
    (ziel / 'tokenizer.json').write_text(json.dumps(tok, ensure_ascii=False), encoding='utf-8')
    werte = []
    for i in range(len(TOKENS)):
        zeile = [0.0] * SPALTEN
        zeile[i] = 2.0  # nicht normiert – wie im echten Modell
        zeile[SPALTEN - 1] = 5.0  # liegt hinter den 32 Dimensionen und fällt beim Umwandeln weg
        werte.extend(zeile)
    kopf = json.dumps({'embedding.weight': {'dtype': 'F32', 'shape': [len(TOKENS), SPALTEN], 'data_offsets': [0, 4 * len(werte)]}}).encode()
    with (ziel / 'model.safetensors').open('wb') as f:
        f.write(struct.pack('<Q', len(kopf)) + kopf + struct.pack(f'<{len(werte)}f', *werte))


if __name__ == '__main__':
    main()
