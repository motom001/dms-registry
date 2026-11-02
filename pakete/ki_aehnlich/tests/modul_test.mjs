// Test des gebauten Moduls (code/modul.wasm) mit einer Nachbildung des DMS: Importe dms.* und WASI, Daten aus einem
// Ordner (wie code/daten/), API-Antworten für ein Dokument mit Volltext. Jeder Aufruf mit frischem Speicher –
// wie im Paket-Läufer, der je Aufruf einen neuen Worker startet und das Modell neu lädt.
//
//   node tests/modul_test.mjs klein <daten>    Tokenizer und Ablauf mit dem kleinen Modell (tests/kleines_modell.py)
//   node tests/modul_test.mjs echt  <daten>    das echte Modell: Ähnlichkeit auf Deutsch, Laufzeit, Speicher
//   node tests/modul_test.mjs gross            Laufzeit mit einem Zufallsmodell in voller Größe (ohne Netz)
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const [art, ordner] = process.argv.slice(2);
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));

/** Ein Aufruf wie im Paket-Läufer; daten: Name → Inhalt (wie code/daten/). */
function lauf(daten, eingabe, { volltext = 'Rechnung', status = 200 } = {}) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 2, maximum: 4096 });  // 256 MB wie im Läufer
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (s, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return s; };
  const api = (q) => {
    aufrufe.push(q);
    let m;
    if (q.methode === 'GET' && (m = /^\/dokumente\/([\w-]+)\/volltext$/.exec(q.pfad))) return status === 200 ? json(200, { id: m[1], name: 'brief.pdf', ocr: {}, text: volltext }) : json(status, { fehler: 'x' });
    if (q.methode === 'PUT' && /^\/dokumente\/[\w-]+\/vektor$/.test(q.pfad)) return json(200, { dokument: 'd', modell: q.body.modell, dimension: q.body.vektor.length });
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    datei: (p, l) => { const d = daten[text(p, l)]; if (!d) return -1; antwort = d; return d.length; },
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const wasi = { fd_write: () => 0, fd_close: () => 0, fd_seek: () => 0, proc_exit: (c) => { throw new Error(`proc_exit ${c}`); } };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52);
  const t0 = performance.now();
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const ein = new TextEncoder().encode(JSON.stringify({ ...eingabe, paket: { id: 'ki_aehnlich', version: '1.0.0' }, einstellungen: {} }));
  const p = inst.exports.dms_puffer(ein.length);
  u8().set(ein, p);
  const code = eingabe.aktion ? inst.exports.dms_aktion(p, ein.length) : inst.exports.dms_ereignis(p, ein.length);
  return { code, ergebnis, protokoll, aufrufe, ms: performance.now() - t0, mb: memory.buffer.byteLength / 1048576 };
}

const ladeDaten = (o) => Object.fromEntries(['modell.dat', 'vokabular.txt', 'zeichen.dat'].map((n) => [n, new Uint8Array(readFileSync(join(o, n)))]));
const vektorZu = (daten, t) => { const r = lauf(daten, { aktion: 'dms:vektor', text: t }); return { ...JSON.parse(r.ergebnis), ms: r.ms, mb: r.mb }; };
const kos = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
let fehler = 0;
const pruefe = (name, ok, info = '') => { if (ok) console.log(`✓ ${name}${info ? ` – ${info}` : ''}`); else { fehler++; console.log(`✗ ${name}${info ? ` – ${info}` : ''}`); } };

if (art === 'klein') {
  const daten = ladeDaten(ordner);
  const tokens = readFileSync(join(ordner, 'vokabular.txt'), 'utf8').trimEnd().split('\n');
  /** Welche Tokens wie oft (Token i hat einen Einheitsvektor in Dimension i). */
  const zaehle = (t) => {
    const v = vektorZu(daten, t).vektor;
    if (!v) return {};
    const min = Math.min(...v.filter((x) => x > 1e-6));
    return Object.fromEntries(v.map((x, i) => [tokens[i], Math.round(x / min)]).filter(([, n]) => n > 0));
  };
  const sortiert = (o) => JSON.stringify(Object.entries(o).sort(([a], [b]) => (a < b ? -1 : 1)));
  const gleich = (name, t, erwartet) => { const ist = zaehle(t); pruefe(name, sortiert(ist) === sortiert(erwartet), `${JSON.stringify(t)} → ${JSON.stringify(ist)}`); };
  gleich('Kleinschreibung, Umlaute ohne Punkte, Satzzeichen als eigene Tokens', 'Prüfung, Gastherme!', { gas: 1, '##therme': 1, prufung: 1, ',': 1, '!': 1 });
  gleich('WordPiece: längster Treffer, Fortsetzung mit ##', 'Handyvertrag Vertrag', { handy: 1, '##vertrag': 1, vertrag: 1 });
  gleich('Unbekanntes Wort ganz als [UNK] (nicht teilweise)', 'Gasxyz', { '[UNK]': 1 });
  gleich('Chinesische Schriftzeichen einzeln, auch ohne Leerzeichen', 'strom中文', { strom: 1, 中: 1, 文: 1 });
  gleich('Leerraum, Steuerzeichen, Zeilenumbrüche', 'die\u0000 \t\nder​\r\nfur', { der: 1, fur: 1, die: 1 });
  gleich('ß bleibt, Œ wird œ – wie der Tokenizer', 'Œ ß', { ß: 1, œ: 1 });
  gleich('Bindestrich trennt', 'Heizung-Wartung', { heizung: 1, wartung: 1, '-': 1 });
  gleich('Zu langes Wort (über 100 Zeichen) ist [UNK]', 'e'.repeat(101), { '[UNK]': 1 });
  gleich('Wiederholung zählt mehrfach', 'Rechnung Rechnung Strom', { rechnung: 2, strom: 1 });
  // Dimensionen hinter den ersten 32 fallen weg (Matryoshka).
  const v = vektorZu(daten, 'Rechnung');
  pruefe('Modellkennung, Länge, normiert, Schwelle', v.modell === 'static-similarity-mrl-multilingual-v1/32' && v.vektor.length === 32 && Math.abs(kos(v.vektor, v.vektor) - 1) < 1e-4 && v.schwelle === 0.45, JSON.stringify({ modell: v.modell, schwelle: v.schwelle }));
  const leer = vektorZu(daten, '');
  pruefe('Leerer Text: nur Modell (so fragt das DMS das Modell ab)', leer.modell && leer.vektor === undefined);
  pruefe('Nur Satzzeichen, die es nicht gibt: [UNK]', JSON.stringify(zaehle('?')) === '{"[UNK]":1}');
  // Ereignis: Volltext holen, Vektor setzen.
  const e = { art: 'volltext.fertig', id: 'e1', versuch: 1, daten: { dokument: '0f8e-1', mappe: 'm1' } };
  const r = lauf(daten, e, { volltext: 'Rechnung für die Heizung' });
  const put = r.aufrufe.find((a) => a.methode === 'PUT');
  pruefe('volltext.fertig → GET Volltext, PUT Vektor', r.code === 0 && r.aufrufe[0].pfad === '/dokumente/0f8e-1/volltext' && put?.pfad === '/dokumente/0f8e-1/vektor' && put.body.vektor.length === 32 && put.body.modell === v.modell, r.ergebnis);
  pruefe('Dokument weg (404): erledigt, kein Fehler', lauf(daten, e, { status: 404 }).code === 0);
  pruefe('DMS antwortet mit Fehler (500): Fehler, das DMS wiederholt', lauf(daten, e, { status: 500 }).code === 1);
  const ohne = lauf(daten, e, { volltext: null });
  pruefe('Ohne Volltext: nichts zu tun', ohne.code === 0 && !ohne.aufrufe.some((a) => a.methode === 'PUT'), ohne.ergebnis);
  pruefe('Andere Ereignisse: nichts zu tun', lauf(daten, { art: 'dokument.hochgeladen', daten: { dokument: 'x' } }).aufrufe.length === 0);
  pruefe('Ungültige Dokument-Id: kein API-Aufruf', lauf(daten, { art: 'volltext.fertig', daten: { dokument: '../typen' } }).aufrufe.length === 0);
  pruefe('Andere Aktion: freundliche Meldung', lauf(daten, { aktion: 'x' }).ergebnis === 'Dieses Paket hat keine Aktionen.');
  pruefe('Ohne Daten: Fehler mit Meldung', lauf({}, { aktion: 'dms:vektor', text: 'a' }).code === 2);
} else if (art === 'echt' || art === 'gross') {
  let daten;
  if (art === 'echt') daten = ladeDaten(ordner);
  else {
    // Zufallsmodell in voller Größe: 105 879 Tokens × 256 Dimensionen, Vokabular mit erfundenen Wortteilen.
    const n = 105879, d = 256;
    const kopf = new Uint32Array([0x56534d44, 1, n, d, 1, 0]);
    const roh = new Uint8Array(24 + n * 4 + n * d);
    roh.set(new Uint8Array(kopf.buffer), 0);
    new Float32Array(roh.buffer, 24, n).fill(0.01);
    for (let i = 24 + n * 4; i < roh.length; i++) roh[i] = (i * 2654435761) >>> 24;
    const silben = ['ver', 'trag', 'rech', 'nung', 'hei', 'zung', 'gas', 'ther', 'me', 'war', 'tung', 'strom', 'kun', 'di', 'gung', 'an', 'be', 'scheid'];
    const tok = ['[PAD]', '[UNK]'];
    for (let i = 2; tok.length < n; i++) { let t = '', x = i; do { t += silben[x % silben.length]; x = Math.floor(x / silben.length); } while (x); tok.push(i % 3 ? t : `##${t}`); }
    daten = { 'modell.dat': roh, 'vokabular.txt': new TextEncoder().encode([...new Set(tok)].concat(Array.from({ length: n - new Set(tok).size }, (_, i) => `x${i}`)).join('\n') + '\n'), 'zeichen.dat': new Uint8Array(readFileSync(ordner ? join(ordner, 'zeichen.dat') : join(hier, '..', 'code', 'daten', 'zeichen.dat'))) };
  }
  const groesse = Object.values(daten).reduce((s, x) => s + x.length, 0);
  console.log(`Daten: ${(groesse / 1048576).toFixed(1)} MB`);
  if (art === 'echt') {
    const a = vektorZu(daten, 'Rechnung für die Heizung');
    const b = vektorZu(daten, 'Wartung der Gastherme');
    const c = vektorZu(daten, 'Kündigung des Handyvertrags');
    const d = vektorZu(daten, 'Invoice for the heating system');
    pruefe('„Rechnung für die Heizung“ liegt näher an „Wartung der Gastherme“ als an „Kündigung des Handyvertrags“', kos(a.vektor, b.vektor) > kos(a.vektor, c.vektor), `${kos(a.vektor, b.vektor).toFixed(3)} > ${kos(a.vektor, c.vektor).toFixed(3)}`);
    pruefe('Deutsch und Englisch: „Invoice for the heating system“ liegt nahe an „Rechnung für die Heizung“', kos(a.vektor, d.vektor) > kos(c.vektor, d.vektor), `${kos(a.vektor, d.vektor).toFixed(3)} > ${kos(c.vektor, d.vektor).toFixed(3)}`);
    console.log(`  Schwelle des Pakets: ${a.schwelle}`);
  }
  // Laufzeit: Suchbegriff und ein langes Dokument (je Aufruf frisch, mit Laden des Modells), Median aus 5.
  const median = (f) => { const t = []; for (let i = 0; i < 5; i++) t.push(f()); t.sort((x, y) => x - y); return t[2]; };
  const such = median(() => vektorZu(daten, 'Rechnung für die Heizung').ms);
  const brief = 'Sehr geehrte Damen und Herren, hiermit erhalten Sie die Rechnung für die Wartung Ihrer Gastherme. '.repeat(500);
  let mb = 0;
  const lang = median(() => { const r = lauf(daten, { art: 'volltext.fertig', daten: { dokument: 'd-1' } }, { volltext: brief }); mb = r.mb; if (r.code) throw new Error(r.ergebnis + r.protokoll); return r.ms; });
  console.log(`  Suchbegriff: ${such.toFixed(0)} ms · Dokument mit ${brief.length.toLocaleString('de-DE')} Zeichen: ${lang.toFixed(0)} ms · Speicher je Aufruf ${mb.toFixed(0)} MB (ohne Start des Workers)`);
  pruefe('Suchbegriff unter 1 s', such < 1000);
} else {
  console.error('Aufruf: node tests/modul_test.mjs klein|echt <daten> | gross'); process.exit(2);
}
if (fehler) { console.log(`${fehler} Fehler`); process.exit(1); }
console.log('Alles gut.');
