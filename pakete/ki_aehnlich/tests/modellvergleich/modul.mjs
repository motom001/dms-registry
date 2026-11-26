// Modellvergleich (registry #242): das Modul dieses Pakets für Vektoren („vektoren“) und „Wohin gehört das?“ („klass <fälle.json>“).
import { readFileSync, writeFileSync } from 'node:fs';
const daten = process.env.DATEN, modul = new WebAssembly.Module(readFileSync(process.env.MODUL));
const D = Object.fromEntries(['modell.dat', 'vokabular.txt', 'zeichen.dat'].map((n) => [n, new Uint8Array(readFileSync(`${daten}/${n}`))]));
export function lauf(eingabe) {
  let antwort = new Uint8Array(0), ergebnis = '';
  const memory = new WebAssembly.Memory({ initial: 2, maximum: 4096 }); const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const dms = { api: () => 404, datei: (p, l) => { const d = D[text(p, l)]; if (!d) return -1; antwort = d; return d.length; },
    antwort_laenge: () => antwort.length, antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; }, log: () => 0 };
  const imp = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') imp.wasi_snapshot_preview1[i.name] = () => 0;
  const inst = new WebAssembly.Instance(modul, imp); inst.exports._initialize?.();
  const ein = new TextEncoder().encode(JSON.stringify({ ...eingabe, paket: { id: 'ki_aehnlich', version: '1' }, einstellungen: {} }));
  const p = inst.exports.dms_puffer(ein.length); u8().set(ein, p); inst.exports.dms_aktion(p, ein.length);
  return JSON.parse(ergebnis);
}
if (process.argv[2] === 'vektoren') {
  const S = JSON.parse(readFileSync('satz.json', 'utf8')); const t0 = Date.now();
  const Dv = S.map((d) => lauf({ aktion: 'dms:vektor', text: d.text }).vektor); const ms = (Date.now() - t0) / S.length;
  const Qv = S.map((d) => lauf({ aktion: 'dms:vektor', text: d.titel || ' ' }).vektor ?? Dv[0].map(() => 0));
  writeFileSync('wasm-256.json', JSON.stringify({ D: Dv, Q: Qv })); console.log('wasm-256', ms.toFixed(1), 'ms/Dok inkl. Laden');
}
if (process.argv[2] === 'klass') {
  const faelle = JSON.parse(readFileSync(process.argv[3], 'utf8')); let geliefert = 0, richtig = 0, fuell = 0;
  for (const f of faelle) { const r = lauf({ aktion: 'dms:klassifizieren', typen: f.typen, aehnliche: f.aehnliche, text: '' });
    if (r.typen?.length) { geliefert++; if (r.typen[0].typ === f.soll) richtig++; else if (r.typen[0].typ === 'finanzen:kontoauszug') fuell++; } }
  console.log(JSON.stringify({ n: faelle.length, geliefert, richtig, fuell }));
}
