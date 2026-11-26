#!/usr/bin/env python3
"""Referenz für tests/nativ.cpp: Wortteile mit dem Tokenizer von Hugging Face (Nummern auf die gekürzte Wortliste
umgerechnet) und Vektor mit dem Modell in 32 Bit (numpy). Eine Zeile JSON je Text (stdin: eine Zeile JSON-String).
    python3 referenz.py <modellordner> <daten> [tokens] < texte.jsonl"""
import json, struct, sys
import numpy as np
from safetensors.numpy import load_file
from tokenizers import Tokenizer

quelle, daten = sys.argv[1], sys.argv[2]
nur_tokens = len(sys.argv) > 3 and sys.argv[3] == 'tokens'
tok = Tokenizer.from_file(f'{quelle}/tokenizer.json'); tok.enable_truncation(256)
vok = json.load(open(f'{quelle}/tokenizer.json'))['model']['vocab']
roh = open(f'{daten}/vokabular.dat', 'rb').read(); n = struct.unpack('<I', roh[8:12])[0]; p = 16; neu = {}
for i in range(n):
    _, l = struct.unpack('<fH', roh[p:p + 6]); p += 6; neu[roh[p:p + l].decode()] = i; p += l
G = None if nur_tokens else load_file(f'{quelle}/model.safetensors')

def ln(x, g, b):
    m = x.mean(-1, keepdims=True); v = ((x - m) ** 2).mean(-1, keepdims=True)
    return (x - m) / np.sqrt(v + 1e-12) * g + b

def gelu(x):
    from math import erf
    return 0.5 * x * (1 + np.vectorize(erf)(x / np.sqrt(2)))

def vektor(ids):
    w = lambda k: G[k]
    L = len(ids)
    x = w('embeddings.word_embeddings.weight')[ids] + w('embeddings.position_embeddings.weight')[:L] + w('embeddings.token_type_embeddings.weight')[0]
    x = ln(x, w('embeddings.LayerNorm.weight'), w('embeddings.LayerNorm.bias'))
    for s in range(12):
        p = f'encoder.layer.{s}.'
        lin = lambda t, h: h @ w(p + t + '.weight').T + w(p + t + '.bias')
        q, k, v = (lin(f'attention.self.{t}', x).reshape(L, 12, 32).transpose(1, 0, 2) for t in ('query', 'key', 'value'))
        a = q @ k.transpose(0, 2, 1) / np.sqrt(32); a = np.exp(a - a.max(-1, keepdims=True)); a /= a.sum(-1, keepdims=True)
        o = (a @ v).transpose(1, 0, 2).reshape(L, 384)
        x = ln(x + lin('attention.output.dense', o), w(p + 'attention.output.LayerNorm.weight'), w(p + 'attention.output.LayerNorm.bias'))
        h = lin('intermediate.dense', x); h = 0.5 * h * (1 + np.tanh(0)) if False else h
        from scipy.special import erf as serf  # noqa
        h = 0.5 * h * (1 + serf(h / np.sqrt(2)))
        x = ln(x + lin('output.dense', h), w(p + 'output.LayerNorm.weight'), w(p + 'output.LayerNorm.bias'))
    v = x.mean(0); return v / np.linalg.norm(v)

for zeile in sys.stdin:
    t = json.loads(zeile); e = tok.encode(t)
    ids = [neu.get(x, 3) for x in e.tokens]
    aus = {'ids': ids}
    if not nur_tokens:
        aus['vektor'] = [float(f) for f in vektor(e.ids)]
    print(json.dumps(aus))
