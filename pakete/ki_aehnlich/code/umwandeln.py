#!/usr/bin/env python3
"""
Bereitet das Embedding-Modell für das Modul vor (läuft beim Bau, nicht im DMS).

    python3 umwandeln.py <ordner mit model.safetensors und tokenizer.json> <zielordner> [dimensionen]

Liest das Modell static-similarity-mrl-multilingual-v1 (sentence-transformers, Apache-2.0): eine Tabelle mit
einem Vektor je Token (105 879 × 1024, float32) und den WordPiece-Tokenizer von bert-base-multilingual-uncased.
Schreibt in den Zielordner (das wird code/daten/):

    modell.dat       Kopf, je Token ein Maßstab (float32) und die ersten <dimensionen> Werte als int8
                     (Matryoshka: das Modell ist darauf trainiert, dass die ersten Dimensionen allein taugen)
    vokabular.txt    die Tokens in der Reihenfolge ihrer Nummer, eines je Zeile
    zeichen.dat      Zeichentabellen wie der Tokenizer: Kleinschreibung ohne Akzente, Leerraum, Steuerzeichen,
                     Satzzeichen, chinesisch-japanisch-koreanische Schriftzeichen

Nur Python ohne weitere Pakete. Prüft, ob Modell und Tokenizer so aufgebaut sind, wie das Modul es erwartet.
"""
import json, struct, sys, unicodedata
from array import array
from pathlib import Path

DIM_STANDARD = 256


def fehler(t: str):
    sys.exit(f'umwandeln.py: {t}')


def tokenizer(pfad: Path) -> tuple[list[str], int]:
    t = json.loads(pfad.read_text(encoding='utf-8'))
    n, v, m = t.get('normalizer') or {}, t.get('pre_tokenizer') or {}, t.get('model') or {}
    if n.get('type') != 'BertNormalizer' or n.get('lowercase') is not True or n.get('strip_accents') not in (None, True) \
            or n.get('clean_text') is not True or n.get('handle_chinese_chars') is not True:
        fehler(f'unerwarteter Normalizer: {n}')
    if v.get('type') != 'BertPreTokenizer':
        fehler(f'unerwarteter Pre-Tokenizer: {v}')
    if m.get('type') != 'WordPiece' or m.get('continuing_subword_prefix') != '##' or m.get('unk_token') != '[UNK]' \
            or m.get('max_input_chars_per_word') != 100:
        fehler(f'unerwartetes Tokenizer-Modell: { {k: m.get(k) for k in ("type", "continuing_subword_prefix", "unk_token", "max_input_chars_per_word")} }')
    vokabular = m['vocab']
    tokens = [''] * len(vokabular)
    for tok, i in vokabular.items():
        if not 0 <= i < len(tokens) or tokens[i] or '\n' in tok:
            fehler(f'Vokabular nicht lückenlos oder mit Zeilenumbruch: {tok!r} → {i}')
        tokens[i] = tok
    return tokens, vokabular['[UNK]']


def tabelle(pfad: Path, anzahl: int, dim: int, ziel: Path):
    with pfad.open('rb') as f:
        laenge = struct.unpack('<Q', f.read(8))[0]
        kopf = json.loads(f.read(laenge))
        namen = [k for k in kopf if k != '__metadata__']
        if len(namen) != 1:
            fehler(f'erwartet genau eine Tabelle in model.safetensors, gefunden: {namen}')
        t = kopf[namen[0]]
        zeilen, spalten = t['shape']
        if t['dtype'] != 'F32' or zeilen != anzahl or spalten < dim:
            fehler(f'Tabelle {t["dtype"]} {t["shape"]} passt nicht (erwartet F32 [{anzahl}, ≥{dim}])')
        start = 8 + laenge + t['data_offsets'][0]
        massstab, werte = array('f'), array('b')
        f.seek(start)
        for _ in range(zeilen):
            zeile = array('f')
            zeile.frombytes(f.read(spalten * 4))
            if sys.byteorder != 'little':
                zeile.byteswap()
            z = zeile[:dim]
            m = max(abs(x) for x in z) or 1.0
            massstab.append(m / 127)
            werte.extend(max(-127, min(127, round(x * 127 / m))) for x in z)
    with ziel.open('wb') as f:
        f.write(b'DMSV' + struct.pack('<5I', 1, anzahl, dim, 0, 0))
        f.write(massstab.tobytes() if sys.byteorder == 'little' else _le(massstab))
        f.write(werte.tobytes())


def _le(a: array) -> bytes:
    b = array(a.typecode, a)
    b.byteswap()
    return b.tobytes()


# Zeichenklassen wie BertPreTokenizer/BertNormalizer (HF tokenizers): 1 Leerraum, 2 Steuerzeichen, 3 Satzzeichen, 4 CJK.
LEER, STEUER, SATZ, CJK = 1, 2, 3, 4
CJK_BEREICHE = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF), (0x2A700, 0x2B73F), (0x2B740, 0x2B81F),
                (0x2B820, 0x2CEAF), (0xF900, 0xFAFF), (0x2F800, 0x2FA1F)]


def klasse(cp: int) -> int:
    c = chr(cp)
    if c in ' \t\n\r' or unicodedata.category(c) == 'Zs':
        return LEER
    if cp in (0, 0xFFFD) or unicodedata.category(c) in ('Cc', 'Cf', 'Cs', 'Co', 'Cn'):  # wie is_control in tokenizers
        return STEUER
    if any(a <= cp <= b for a, b in CJK_BEREICHE):
        return CJK
    if 33 <= cp <= 47 or 58 <= cp <= 64 or 91 <= cp <= 96 or 123 <= cp <= 126 or unicodedata.category(c).startswith('P'):
        return SATZ
    return 0


def zeichen(ziel: Path):
    abbildung, bereiche = [], []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        k = klasse(cp)
        if k and bereiche and bereiche[-1][2] == k and bereiche[-1][1] == cp - 1:
            bereiche[-1][1] = cp
        elif k:
            bereiche.append([cp, cp, k])
        if k:
            continue
        # Kleinschreibung, dann Akzente weg (NFD ohne Zeichen der Klasse Mn) – wie BertNormalizer mit lowercase.
        m = ''.join(x for x in unicodedata.normalize('NFD', chr(cp).lower()) if unicodedata.category(x) != 'Mn')
        if m != chr(cp):
            if len(m) > 3:
                fehler(f'U+{cp:04X} wird zu {len(m)} Zeichen')
            abbildung.append((cp, [ord(x) for x in m]))
    with ziel.open('wb') as f:
        f.write(b'DMSZ' + struct.pack('<3I', 1, len(abbildung), len(bereiche)))
        for cp, aus in abbildung:
            f.write(struct.pack('<5I', cp, len(aus), *(aus + [0, 0, 0])[:3]))
        for von, bis, k in bereiche:
            f.write(struct.pack('<3I', von, bis, k))
    return len(abbildung), len(bereiche)


def main():
    if len(sys.argv) < 3:
        fehler('Aufruf: umwandeln.py <quelle> <ziel> [dimensionen]')
    quelle, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    dim = int(sys.argv[3]) if len(sys.argv) > 3 else DIM_STANDARD
    ziel.mkdir(parents=True, exist_ok=True)
    tokens, unk = tokenizer(quelle / 'tokenizer.json')
    tabelle(quelle / 'model.safetensors', len(tokens), dim, ziel / 'modell.dat')
    # UNK-Nummer in den Kopf (Feld 4).
    with (ziel / 'modell.dat').open('r+b') as f:
        f.seek(16)
        f.write(struct.pack('<I', unk))
    (ziel / 'vokabular.txt').write_text('\n'.join(tokens) + '\n', encoding='utf-8')
    n, b = zeichen(ziel / 'zeichen.dat')
    print(f'  Modell: {len(tokens)} Tokens × {dim} Dimensionen; Zeichen: {n} Abbildungen, {b} Bereiche (Unicode {unicodedata.unidata_version})')


if __name__ == '__main__':
    main()
