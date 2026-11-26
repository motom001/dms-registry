# Modellvergleich (dms-registry #242)

Misst Modelle für „Wohin gehört das?“ und die Suche am **privaten** Satz „Lebensläufe“ (motom001/demo_lebenslaeufe). Nicht Teil der CI. Ergebnis: README des Pakets, Abschnitt „Das Modell“.

Alles läuft in einem Arbeitsordner (aktueller Ordner); Modelle von Hugging Face liegen dort unter `hf/mrl`, `hf/potion` (je `model.safetensors`, `tokenizer.json`) und `hf/e5` (`model.onnx`, `tokenizer.json` aus `onnx/`). Python braucht `numpy tokenizers safetensors onnxruntime`.

```sh
SATZ=…/demo_lebenslaeufe PRUEFSTAND=…/dms/server/werkzeuge/pruefstand MV=. node satz_export.mjs   # → satz.json
DATEN=…/code/daten MODUL=…/code/modul.wasm node modul.mjs vektoren                                 # → wasm-256.json (Modell im Paket)
python3 -c "import json,numpy as n;d=json.load(open('wasm-256.json'));f=lambda X:X/n.maximum(n.linalg.norm(X,axis=1,keepdims=True),1e-9);n.savez('wasm-256.npz',D=f(n.array(d['D'],n.float32)),Q=f(n.array(d['Q'],n.float32)))"
python3 einbetten.py mrl-256 mrl-512 mrl-1024 potion-256 e5-small                               # → <modell>.npz
DATEN=… MODUL=… python3 auswerten.py wasm-256 mrl-256 mrl-512 mrl-1024 potion-256 e5-small
```

Die Ähnlichkeiten jedes Modells werden über die Quantile aller Paare auf die Verteilung des Modells im Paket abgebildet, damit Schwelle (0,45) und „nah“ (0,85) des Pakets für alle gleich gelten.
