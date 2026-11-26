// Tests des Moduls mit dem echten Modell (nach code/bauen.sh): Vektoren gegen die Referenz in 32 Bit (tests/erwartung.json,
// prüft Tokenizer, Normalisierung und Transformer zusammen), Ähnlichkeit auf Deutsch und Englisch, Art des Textes,
// „Wohin gehört das?“, Zeit und Speicher.
//   node tests/modul_test.mjs [code/daten]
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PAKET = join(dirname(fileURLToPath(import.meta.url)), '..');
const DATEN = process.argv[2] ?? join(PAKET, 'code/daten');
const modul = new WebAssembly.Module(readFileSync(join(PAKET, 'code/modul.wasm')));
const D = Object.fromEntries(['modell.dat', 'vokabular.dat', 'normal.dat'].map((n) => [n, new Uint8Array(readFileSync(join(DATEN, n)))]));
let fehler = 0, spitze = 0;
const pruefe = (name, ok, info = '') => { console.log(`${ok ? 'ok  ' : 'FEHLER'} ${name}${info ? ` – ${info}` : ''}`); if (!ok) fehler++; };

function lauf(eingabe, { ereignis = false, api = () => [404, ''] } = {}) {
  let antwort = new Uint8Array(0), ergebnis = '';
  const aufrufe = [];
  const memory = new WebAssembly.Memory({ initial: 2, maximum: 4096 });  // 256 MB wie der Läufer
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const dms = {
    api: (p, l) => { const q = JSON.parse(text(p, l)); aufrufe.push(q); const [s, t] = api(q); antwort = new TextEncoder().encode(t); return s; },
    datei: (p, l) => { const d = D[text(p, l)]; if (!d) return -1; antwort = d; return d.length; },
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: () => 0,
  };
  const imp = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') imp.wasi_snapshot_preview1[i.name] = () => 0;
  const inst = new WebAssembly.Instance(modul, imp);
  inst.exports._initialize?.();
  const ein = new TextEncoder().encode(JSON.stringify(eingabe));
  const p = inst.exports.dms_puffer(ein.length);
  u8().set(ein, p);
  const a = Date.now();
  const code = (ereignis ? inst.exports.dms_ereignis : inst.exports.dms_aktion)(p, ein.length);
  spitze = Math.max(spitze, memory.buffer.byteLength);
  return { code, ergebnis, aufrufe, ms: Date.now() - a };
}
const vektor = (text, art) => { const r = lauf({ aktion: 'dms:vektor', text, ...(art ? { art } : {}) }); return { ...r, ...JSON.parse(r.ergebnis) }; };
const kos = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);

// 1. Gegen die Referenz in 32 Bit: Kosinus ≥ 0,99 (int8 und gekürzte Wortliste kosten wenig).
const erw = JSON.parse(readFileSync(join(PAKET, 'tests/erwartung.json'), 'utf8'));
let schlechteste = 1;
for (const { text, vektor: soll } of erw.texte) {
  const suche = text.startsWith('query: ');
  const v = vektor(text.slice(suche ? 7 : 9), suche ? 'suche' : 'dokument').vektor;
  schlechteste = Math.min(schlechteste, kos(v, soll));
}
pruefe('Vektoren wie die Referenz in 32 Bit (Kosinus ≥ 0,99)', schlechteste >= 0.99, schlechteste.toFixed(4));

// 2. Ähnlichkeit: Suchbegriff → passendes Dokument vor unpassendem, auch auf Englisch.
const q = vektor('Rechnung für die Heizung', 'suche').vektor;
const wartung = vektor('Wartung der Gastherme durch die Firma Beispiel GmbH', 'dokument').vektor;
const handy = vektor('Kündigung des Handyvertrags zum 31.12.2026', 'dokument').vektor;
pruefe('„Rechnung für die Heizung“ näher an der Wartung der Gastherme als am Handyvertrag', kos(q, wartung) > kos(q, handy), `${kos(q, wartung).toFixed(3)} > ${kos(q, handy).toFixed(3)}`);
const en = vektor('Invoice for the heating maintenance', 'suche').vektor;
pruefe('Englischer Suchbegriff findet das deutsche Dokument', kos(en, wartung) > kos(en, handy));

// 3. Art des Textes (DMS #1706): „suche“ und „dokument“ geben verschiedene Vektoren; ohne Art entscheidet die Länge.
const s1 = vektor('Wartung der Gastherme', 'suche').vektor, d1 = vektor('Wartung der Gastherme', 'dokument').vektor, o1 = vektor('Wartung der Gastherme').vektor;
pruefe('Suchbegriff und Dokument mit eigenem Vorsatz', kos(s1, d1) < 0.999 && kos(s1, o1) > 0.9999);
const lang = 'Wartung der Gastherme. '.repeat(20);
pruefe('ohne Art: langer Text gilt als Dokument', kos(vektor(lang).vektor, vektor(lang, 'dokument').vektor) > 0.9999);

// 4. Modellabfrage ohne Text: Kennung und Schwelle, ohne das Modell zu laden.
const leer = vektor('');
pruefe('Modellabfrage ohne Text', leer.modell === 'multilingual-e5-small/384-int8-256' && leer.schwelle === 0.85 && !leer.vektor && leer.ms < 50, `${leer.ms} ms`);

// 5. Ereignis volltext.fertig: Volltext holen, Vektor speichern.
const id = '0f0e0d0c-0b0a-4908-8706-050403020100';
const ev = lauf({ art: 'volltext.fertig', daten: { dokument: id } }, {
  ereignis: true,
  api: (q2) => q2.methode === 'GET' ? [200, JSON.stringify({ text: 'Rechnung über die Wartung der Gastherme' })] : [200, '{}'],
});
const put = ev.aufrufe.find((a) => a.methode === 'PUT');
pruefe('volltext.fertig speichert einen Vektor mit 384 Werten', ev.code === 0 && put?.pfad === `/dokumente/${id}/vektor` && put.body.vektor.length === 384 && put.body.modell === leer.modell, ev.ergebnis);
pruefe('volltext.fertig rechnet als Dokument', kos(put.body.vektor, vektor('Rechnung über die Wartung der Gastherme', 'dokument').vektor) > 0.9999);

// 6. Wohin gehört das? – Schwellen dieses Modells.
const typen = [{ id: 'w', name: 'Wartung', anzahl: 3 }, { id: 'r', name: 'Rechnung', anzahl: 40 }];
let k = JSON.parse(lauf({ aktion: 'dms:klassifizieren', typen, aehnliche: [{ typ: 'w', aehnlichkeit: 0.97 }, ...Array(8).fill({ typ: 'r', aehnlichkeit: 0.87 })] }).ergebnis);
pruefe('Klassifizieren: eine sehr nahe Mappe schlägt viele mittelmäßige', k.typen[0]?.typ === 'w' && k.typen[0].begruendung === 'Sehr ähnlich zu einer Mappe in Wartung', JSON.stringify(k));
k = JSON.parse(lauf({ aktion: 'dms:klassifizieren', typen, aehnliche: [{ typ: 'w', aehnlichkeit: 0.84 }] }).ergebnis);
pruefe('Klassifizieren: unter der Schwelle kein Vorschlag', k.typen.length === 0);

// 7. Zeit und Speicher mit langem Text (256 Wortteile, Laden des Modells eingeschlossen).
const t = vektor('Rechnung Wartung Gastherme Heizung Betrag Datum Kunde Anschrift '.repeat(200), 'dokument');
pruefe('langer Text: höchstens 3 s', t.ms < 3000, `${t.ms} ms`);
pruefe('Speicher des Moduls unter 200 MB', spitze < 200 * 2 ** 20, `${(spitze / 2 ** 20).toFixed(0)} MB`);
const s = vektor('Heizung', 'suche');
pruefe('Suchbegriff: höchstens 1 s', s.ms < 1000, `${s.ms} ms`);

console.log(fehler ? `${fehler} Fehler.` : 'Alles gut.');
process.exitCode = fehler ? 1 : 0;
