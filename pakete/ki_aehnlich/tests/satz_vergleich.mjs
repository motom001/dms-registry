// Offline-Messung für „Wohin gehört das?“ (registry #265, #242): der private Satz „Lebensläufe“ wie im Lernlauf des
// Prüfstands (motom001/dms, server/werkzeuge/pruefstand): Dokumente nach Datum, jedes sieht die Mappen der Dokumente davor
// (je Mappe das beste Dokument, höchstens 10, ab der Schwelle), mit Zahl der Mappen je Typ. Vergleicht Fassungen des
// Moduls mit denselben Vektoren (aus der ersten Fassung). Nicht Teil der CI – der Satz ist privat.
//
//   node tests/satz_vergleich.mjs <satz> <code/daten> <prüfstand-ordner> alt.wasm neu.wasm […]
//   AUFFUELLEN=200 …   Ungleichgewicht (#1672): vorher 200 Kontoauszug-Mappen (Vektoren der Kontoauszüge des Satzes
//                      reihum), gemessen werden dann nur die übrigen Dokumente.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const [satzOrdner, daten, pruefstand, ...module] = process.argv.slice(2);
const { liesSatz, typKennung } = await import(join(pruefstand, 'satz.mjs'));
const D = Object.fromEntries(['modell.dat', 'vokabular.txt', 'zeichen.dat'].map((n) => [n, new Uint8Array(readFileSync(`${daten}/${n}`))]));
function lauf(modul, eingabe) {
  let antwort = new Uint8Array(0), ergebnis = '';
  const memory = new WebAssembly.Memory({ initial: 2, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
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
const mods = module.map((f) => new WebAssembly.Module(readFileSync(f)));
const satz = liesSatz(satzOrdner);
const doks = satz.dokumente.filter((d) => d.erwartung.mappe !== 'keine' && satz.mappen.get(d.erwartung.mappe));
const body = (d) => readFileSync(d.md, 'utf8').replace(/^---\n[\s\S]*?\n---\n/, '');
const cache = join(tmpdir(), 'ki_aehnlich-satz-vektoren.json');
let vek = existsSync(cache) ? JSON.parse(readFileSync(cache, 'utf8')) : {};
for (const d of doks) if (!vek[d.id]) vek[d.id] = lauf(mods[0], { aktion: 'dms:vektor', text: body(d) }).vektor;
writeFileSync(cache, JSON.stringify(vek));
const kos = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const typ = (d) => typKennung(satz, satz.mappen.get(d.erwartung.mappe).typ);
const SCHWELLE = 0.45;
const st = mods.map(() => ({ geliefert: 0, richtig: 0, fuell: 0 }));
const FUELL = 'finanzen:kontoauszug', fuellN = Number(process.env.AUFFUELLEN ?? 0);
const fuellVek = doks.filter((d) => typ(d) === FUELL).map((d) => vek[d.id]);
const fuell = fuellN ? Array.from({ length: fuellN }, (_, i) => ({ mappe: `fuell-${i}`, typ: FUELL, v: fuellVek[i % fuellVek.length] })) : [];
const alleTypen = [...new Set(doks.map(typ))];
for (let i = 0; i < doks.length; i++) {
  const d = doks[i];
  if (fuellN && typ(d) === FUELL) continue;
  const best = new Map();
  for (const f of fuell) { const s = kos(vek[d.id], f.v); if (s >= SCHWELLE) best.set(f.mappe, { s, typ: f.typ }); }
  for (let j = 0; j < i; j++) {
    const m = doks[j].erwartung.mappe, s = kos(vek[d.id], vek[doks[j].id]);
    if (s >= SCHWELLE && (!best.has(m) || best.get(m).s < s)) best.set(m, { s, typ: typ(doks[j]) });
  }
  const aehnliche = [...best.values()].sort((a, b) => b.s - a.s).slice(0, 10).map((x) => ({ typ: x.typ, aehnlichkeit: Math.round(x.s * 1000) / 1000 }));
  const anzahl = {};
  for (let j = 0; j < i; j++) anzahl[typ(doks[j])] = (anzahl[typ(doks[j])] ??= new Set()).add(doks[j].erwartung.mappe);
  if (fuellN) anzahl[FUELL] = new Set([...(anzahl[FUELL] ?? []), ...fuell.map((f) => f.mappe)]);
  const typen = alleTypen.map((t) => ({ id: t, name: t, anzahl: anzahl[t]?.size ?? 0 }));
  mods.forEach((m, k) => {
    const r = lauf(m, { aktion: 'dms:klassifizieren', typen, aehnliche, text: '' });
    if (r.typen?.length) { st[k].geliefert++; if (r.typen[0].typ === typ(d)) st[k].richtig++; else if (r.typen[0].typ === FUELL) st[k].fuell++; }
  });
}
module.forEach((f, k) => console.log(`${f}${fuellN ? ` (aufgefüllt ${fuellN})` : ''}: geliefert ${st[k].geliefert}, richtig vorn ${st[k].richtig} (${(100 * st[k].richtig / Math.max(1, st[k].geliefert)).toFixed(1)} %)${fuellN ? `, Kontoauszug fälschlich vorn ${st[k].fuell}` : ''}`));
