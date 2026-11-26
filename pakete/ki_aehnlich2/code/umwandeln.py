#!/usr/bin/env python3
"""
Bereitet multilingual-e5-small (intfloat, MIT) für das Modul vor (läuft beim Bau, nicht in Ablago).

    python3 umwandeln.py <ordner mit model.safetensors und tokenizer.json> <zielordner>

Das Modell ist ein BERT-Transformer (12 Schichten, 384 breit, 12 Köpfe, 1536 im Zwischenschritt) mit dem
SentencePiece-Tokenizer von XLM-RoBERTa (Unigram, 250 002 Wortteile). Schreibt in den Zielordner (→ code/daten/):

    modell.dat      Kopf „DMSE“, dann alle Gewichte: Wortteil-Vektoren und Matrizen als int8 mit einem Maßstab
                    (float32) je Zeile, Positionen, Normierungen und Verschiebungen als float32
    vokabular.dat   Kopf „DMSW“, je Wortteil Bewertung (float32), Länge (u16) und UTF-8 – nur Wortteile aus
                    lateinischer, griechischer und kyrillischer Schrift, Ziffern, Satz- und Sonderzeichen (gut
                    150 000 von 250 002); die Nummern sind neu vergeben, die Vektoren folgen dieser Reihenfolge
    normal.dat      Kopf „DMSN“, Zeichen, die die Normalisierung des Tokenizers ändert (NFKC, Leerraum, Steuerzeichen),
                    je Eintrag Zeichen (u32), Länge (u16) und UTF-8 der Ersetzung; dazu Paare Buchstabe + Akzent →
                    zusammengesetztes Zeichen (je drei u32) – alles erzeugt mit dem Tokenizer selbst

Braucht numpy, safetensors und tokenizers (nur beim Bau).
"""
import json, struct, sys, unicodedata
from pathlib import Path
import numpy as np
from safetensors.numpy import load_file
from tokenizers import Tokenizer

SCHICHTEN, BREITE, ZWISCHEN, POSITIONEN = 12, 384, 1536, 512


def fehler(t):
    sys.exit(f'umwandeln.py: {t}')


def erlaubt(c: str) -> bool:
    if c == '▁':
        return True
    kat = unicodedata.category(c)
    if kat[0] in 'NPSZ':
        return ord(c) < 0x3000
    n = unicodedata.name(c, '')
    return 'LATIN' in n or 'GREEK' in n or 'CYRILLIC' in n


def int8(m: np.ndarray, aus):
    m = m.astype(np.float32)
    s = np.abs(m).max(axis=1) / 127.0
    s[s == 0] = 1.0
    q = np.clip(np.rint(m / s[:, None]), -127, 127).astype(np.int8)
    aus.write(s.astype('<f4').tobytes()); aus.write(q.tobytes())


def f32(m, aus):
    aus.write(np.asarray(m, dtype='<f4').tobytes())


def main():
    if len(sys.argv) != 3:
        fehler('Aufruf: umwandeln.py <modellordner> <zielordner>')
    quelle, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    ziel.mkdir(parents=True, exist_ok=True)
    tj = json.loads((quelle / 'tokenizer.json').read_text(encoding='utf-8'))
    m = tj['model']
    if m.get('type') != 'Unigram' or m.get('unk_id') != 3 or tj['pre_tokenizer'].get('type') != 'Metaspace':
        fehler('unerwarteter Tokenizer (erwartet Unigram, unk 3, Metaspace)')
    vokabular = m['vocab']
    behalten = [i for i, (p, _) in enumerate(vokabular) if i < 4 or all(erlaubt(c) for c in p)]
    neu = {alt: n for n, alt in enumerate(behalten)}

    g = load_file(str(quelle / 'model.safetensors'))
    w = lambda k: g[k]
    emb = w('embeddings.word_embeddings.weight')
    if emb.shape != (len(vokabular) + 35, BREITE) and emb.shape[1] != BREITE:
        fehler(f'Wortteil-Tabelle {emb.shape} passt nicht')
    with open(ziel / 'modell.dat', 'wb') as aus:
        aus.write(b'DMSE' + struct.pack('<6I', 1, len(behalten), BREITE, SCHICHTEN, ZWISCHEN, POSITIONEN))
        int8(emb[behalten], aus)
        f32(w('embeddings.position_embeddings.weight')[:POSITIONEN], aus)
        f32(w('embeddings.token_type_embeddings.weight')[0], aus)
        f32(w('embeddings.LayerNorm.weight'), aus); f32(w('embeddings.LayerNorm.bias'), aus)
        for s in range(SCHICHTEN):
            p = f'encoder.layer.{s}.'
            for teil in ('attention.self.query', 'attention.self.key', 'attention.self.value', 'attention.output.dense'):
                int8(w(p + teil + '.weight'), aus); f32(w(p + teil + '.bias'), aus)
            f32(w(p + 'attention.output.LayerNorm.weight'), aus); f32(w(p + 'attention.output.LayerNorm.bias'), aus)
            int8(w(p + 'intermediate.dense.weight'), aus); f32(w(p + 'intermediate.dense.bias'), aus)
            int8(w(p + 'output.dense.weight'), aus); f32(w(p + 'output.dense.bias'), aus)
            f32(w(p + 'output.LayerNorm.weight'), aus); f32(w(p + 'output.LayerNorm.bias'), aus)

    with open(ziel / 'vokabular.dat', 'wb') as aus:
        aus.write(b'DMSW' + struct.pack('<3I', 1, len(behalten), neu[3]))
        for alt in behalten:
            p, s = vokabular[alt]
            b = p.encode('utf-8')
            aus.write(struct.pack('<fH', float(s), len(b)) + b)

    # Normalisierung Zeichen für Zeichen mit dem Tokenizer selbst (Precompiled-Tabelle von SentencePiece, NFKC).
    tok = Tokenizer.from_file(str(quelle / 'tokenizer.json'))
    eintraege = []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        c = chr(cp)
        if unicodedata.category(c) == 'Cn' and cp > 0xFFFF:
            continue
        n = tok.normalizer.normalize_str('#' + c + '#')
        if not (n.startswith('#') and n.endswith('#')):
            fehler(f'Normalisierung von U+{cp:04X} unerwartet: {n!r}')
        n = n[1:-1]
        if n != c:
            eintraege.append((cp, n.encode('utf-8')))
    # Zerlegte Zeichen (Buchstabe + Akzent, etwa aus PDFs) setzt NFKC zusammen: Paare für die lateinischen,
    # griechischen und kyrillischen Grundbuchstaben mit den kombinierenden Zeichen U+0300–U+036F.
    paare = []
    basis = [chr(c) for c in range(0x41, 0x530) if unicodedata.category(chr(c))[0] == 'L']
    for b in basis:
        for z in range(0x300, 0x370):
            n = tok.normalizer.normalize_str(b + chr(z))
            if len(n) == 1 and n != b:
                paare.append((ord(b), z, ord(n)))
    with open(ziel / 'normal.dat', 'wb') as aus:
        aus.write(b'DMSN' + struct.pack('<3I', 1, len(eintraege), len(paare)))
        for cp, b in eintraege:
            aus.write(struct.pack('<IH', cp, len(b)) + b)
        for p in paare:
            aus.write(struct.pack('<3I', *p))
    groesse = sum((ziel / n).stat().st_size for n in ('modell.dat', 'vokabular.dat', 'normal.dat'))
    print(f'{len(behalten)} von {len(vokabular)} Wortteilen, {len(eintraege)} Zeichen und {len(paare)} Paare in der Normalisierung, {groesse / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
