// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: zwei erfundene Scanseiten (eine
// aufrecht, eine quer gescannt), Ereignis „Volltext fertig“, Seitenbilder über GET …/seiten/{nr}/scan, Volltext über
// PUT …/volltext. Prüft Text, Sprache und die Wortpositionen (#631): jedes Wort relativ zur Seite, wie das DMS sie
// liefert – auch auf der Seite, die das Paket zum Lesen gedreht hat. Dazu die Mappentypen (dms-registry #105): „Nur diese
// Mappentypen“ und „Diese Mappentypen ausschließen“.
//
//   node tests/modul_test.mjs <ordner mit seite-1.pgm, seite-2.pgm, woerter.json aus tests/beispiele.py>
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const ordner = process.argv[2];
if (!ordner) { console.error('Aufruf: node tests/modul_test.mjs <ordner>'); process.exit(2); }
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const DATEN = join(hier, '..', 'code', 'daten');
const soll = JSON.parse(readFileSync(join(ordner, 'woerter.json'), 'utf8'));

function lauf({ volltext = 200, einstellungen = {}, daten = {}, mappentyp = 'basis:rechnung', scans = true } = {}) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const geschrieben = [];
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    const s = /^\/dokumente\/dok-1\/seiten\/(\d+)\/scan\?dpi=\d+$/.exec(q.pfad);
    if (q.methode === 'GET' && q.pfad === '/mappen/mappe-1') return json(200, { id: 'mappe-1', typId: mappentyp });
    if (q.methode === 'GET' && s) {
      if (!scans) return json(404, { fehler: 'Seite gibt es nicht' });
      const f = join(ordner, `seite-${s[1]}.pgm`);
      if (!existsSync(f)) return json(404, { fehler: 'Seite gibt es nicht' });
      antwort = new Uint8Array(readFileSync(f));
      return 200;
    }
    if (q.methode === 'PUT' && q.pfad === '/dokumente/dok-1/volltext') {
      geschrieben.push(q.body);
      if (volltext === 413 && q.body.woerter) return json(413, { fehler: 'Der Körper ist zu groß.' });
      return json(200, { id: 'dok-1' });
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    datei: (p, l) => { const n = text(p, l); const f = join(DATEN, n); if (n.includes('/') || !existsSync(f)) return -1; antwort = new Uint8Array(readFileSync(f)); return antwort.length; },
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const dv = () => new DataView(memory.buffer);
  const wasi = {
    fd_write: (fd, iov, n, aus) => { let s = 0; for (let i = 0; i < n; i++) { const p = dv().getUint32(iov + 8 * i, true), l = dv().getUint32(iov + 8 * i + 4, true); protokoll.push(`stdout ${text(p, l)}`); s += l; } dv().setUint32(aus, s, true); return 0; },
    clock_time_get: (_id, _p, aus) => { dv().setBigUint64(aus, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; },
    environ_get: () => 0,
    fd_prestat_get: () => 8 /* EBADF: keine vorgeöffneten Ordner */,
    proc_exit: (c) => { throw new Error(`proc_exit ${c}`); },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) {
    if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52 /* ENOSYS */);
  }
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const ereignis = new TextEncoder().encode(JSON.stringify({
    art: 'volltext.fertig', id: 'e-1', versuch: 1, erstellt: new Date().toISOString(),
    daten: { dokument: 'dok-1', mappe: 'mappe-1', mime: 'application/pdf', quelle: 'kern', text: false, seiten: 2, ...daten },
    paket: { id: 'texterkennung', version: '2.2.0' }, einstellungen: { sprache: 'Automatisch', drehen: true, max_seiten: 100, dpi: 300, ...einstellungen },
  }));
  const p = inst.exports.dms_puffer(ereignis.length);
  u8().set(ereignis, p);
  const t0 = Date.now();
  let code;
  try { code = inst.exports.dms_ereignis(p, ereignis.length); } catch (f) { code = `Abbruch (${f.message})`; }
  return { code, ergebnis, protokoll, aufrufe, geschrieben, ms: Date.now() - t0 };
}

let fehler = 0;
function pruefe(name, ok, r, mehr = '') {
  if (!ok) { fehler++; console.log(`✗ ${name}: Code ${r.code}, ${r.ergebnis} ${mehr}\n  ${r.aufrufe.join('\n  ')}\n  ${r.protokoll.slice(-10).join('\n  ')}`); }
  else console.log(`✓ ${name}: ${r.ergebnis} (${r.ms} ms)`);
}

let r = lauf();
const b = r.geschrieben.at(-1);
pruefe('Volltext mit Wortpositionen je Seite', r.code === 0 && b && Array.isArray(b.woerter) && b.woerter.length === 2 && b.text.split('\f').length === 2, r);
// Jedes erwartete Wort: in der Liste seiner Seite, Lage höchstens 1,5 % der Seite daneben (Tesseract schneidet enger
// als die Schrift-Kästen von Pillow).
for (const [i, seite] of soll.entries()) {
  const ist = b?.woerter?.[i] ?? [];
  const fehlt = [], daneben = [];
  for (const [t, x, y, w, h] of seite) {
    const k = ist.filter((x2) => x2[0] === t);
    if (!k.length) { fehlt.push(t); continue; }
    const ab = Math.min(...k.map(([, x2, y2, w2, h2]) => Math.max(Math.abs(x2 - x), Math.abs(y2 - y), Math.abs(x2 + w2 - x - w), Math.abs(y2 + h2 - y - h))));
    if (ab > 0.015) daneben.push(`${t} ${(ab * 100).toFixed(1)} %`);
  }
  pruefe(`Seite ${i + 1}${i === 1 ? ' (quer gescannt, zum Lesen gedreht)' : ''}: ${seite.length} Wörter erkannt`, fehlt.length <= 1, r, `fehlt: ${fehlt.join(', ')}`);
  pruefe(`Seite ${i + 1}: Wörter an ihrer Stelle auf der Seite, wie das DMS sie liefert`, !daneben.length, r, daneben.join(', '));
  pruefe(`Seite ${i + 1}: Lage innerhalb der Seite (0…1)`, ist.every(([, x2, y2, w2, h2]) => x2 >= 0 && y2 >= 0 && w2 > 0 && h2 > 0 && x2 + w2 <= 1.00001 && y2 + h2 <= 1.00001), r);
}
r = lauf({ volltext: 413 });
pruefe('Ältere DMS (413 mit Wortpositionen): Text ohne sie', r.code === 0 && r.geschrieben.length === 2 && !r.geschrieben[1].woerter && r.ergebnis.includes('ohne Wortpositionen'), r);

// Mappentypen (dms-registry #105). Ohne Scans (scans: false) endet ein erlaubtes Dokument gleich nach dem Versuch, die
// erste Seite zu holen – das zeigt, dass das Paket es erkennen wollte. Ein ausgelassenes Dokument endet mit Erfolg
// (Code 0) und ohne Volltext; Ablago wartet dann nicht mehr auf die Texterkennung.
const SCAN = 'GET /dokumente/dok-1/seiten/1/scan?dpi=300';
const erkannt = (r) => r.code === 0 && r.aufrufe.includes(SCAN);
const ausgelassen = (r, grund) => r.code === 0 && !r.aufrufe.includes(SCAN) && !r.geschrieben.length && r.ergebnis === grund;
const typ = (t) => ({ daten: { typ: t }, scans: false });
const fall = (name, einstellungen, t, soll, grund) => {
  const r2 = lauf({ ...typ(t), einstellungen });
  pruefe(name, soll ? erkannt(r2) : ausgelassen(r2, grund), r2);
  return r2;
};
fall('Mappentypen: beide leer – erkannt', {}, 'basis:rechnung', true);
fall('Mappentypen: leer + Ausschluss – ausgeschlossener Typ ausgelassen', { typen: [], ohne_typen: ['basis:rechnung', 'basis:vertrag'] }, 'basis:rechnung', false, 'Mappentyp ausgeschlossen');
fall('Mappentypen: leer + Ausschluss – anderer Typ erkannt', { typen: [], ohne_typen: ['basis:rechnung'] }, 'haushalt:urkunde', true);
fall('Mappentypen: gefüllt + Ausschluss – gewählter Typ erkannt', { typen: ['basis:rechnung'], ohne_typen: ['basis:vertrag'] }, 'basis:rechnung', true);
fall('Mappentypen: gefüllt + Ausschluss – ausgeschlossener Typ ausgelassen', { typen: ['basis:rechnung'], ohne_typen: ['basis:vertrag'] }, 'basis:vertrag', false, 'Mappentyp ausgeschlossen');
fall('Mappentypen: gefüllt + Ausschluss – nicht gewählter Typ ausgelassen', { typen: ['basis:rechnung'], ohne_typen: ['basis:vertrag'] }, 'haushalt:urkunde', false, 'Mappentyp nicht gewählt');
fall('Mappentypen: Ausschluss gewinnt, falls ein Typ doch in beiden steht', { typen: ['basis:rechnung'], ohne_typen: ['basis:rechnung'] }, 'basis:rechnung', false, 'Mappentyp ausgeschlossen');
fall('Mappentypen: alte Form der Auswahl ({ typ }) gilt weiter', { typen: [{ typ: 'basis:rechnung' }] }, 'basis:vertrag', false, 'Mappentyp nicht gewählt');
r = fall('Mappentypen: Typ aus dem Ereignis – Mappe nicht gelesen', { ohne_typen: ['basis:vertrag'] }, 'basis:rechnung', true);
pruefe('Mappentypen: Typ aus dem Ereignis – kein GET /mappen', !r.aufrufe.some((a) => a.startsWith('GET /mappen/')), r);
r = lauf({ einstellungen: { ohne_typen: ['basis:rechnung'] }, mappentyp: 'basis:rechnung', scans: false });
pruefe('Mappentypen: ohne Typ im Ereignis liest das Paket die Mappe', ausgelassen(r, 'Mappentyp ausgeschlossen') && r.aufrufe.includes('GET /mappen/mappe-1'), r);
process.exit(fehler ? 1 : 0);
