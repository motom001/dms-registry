// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung von Ablago: Importe dms.* und WASI,
// Rechnungen und Positionen, Status, Umsatzsteuer, Summenprüfung als Hinweis, zeitplan.ausgefuehrt.
//
//   node tests/modul_test.mjs
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const E = (b) => ({ betrag: b, waehrung: 'EUR' });

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher, Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf({ art = 'mappe.geaendert', daten = {}, mappen = {}, konflikt = false, einstellungen = { summenpruefung: true }, erstellt = '2026-11-10T06:00:00.000Z' }) {
  const aufrufe = [], geschrieben = {}, protokoll = [], hinweise = {};
  let antwort = new Uint8Array(0), ergebnis = '';
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    if (q.methode === 'GET' && q.pfad === '/typen') return json(200, [{ id: 't-r', schluessel: 'rechnungen_rechnung' }, { id: 't-p', schluessel: 'rechnungen_rechnungsposition' }]);
    let h = /^\/mappen\/([^/?]+)\/hinweise\/summe$/.exec(q.pfad);
    if (h) { hinweise[h[1]] = q.methode === 'PUT' ? q.body.text : null; return json(200, {}); }
    let m = /^\/mappen\/([^/?]+)$/.exec(q.pfad);
    if (m && q.methode === 'GET') return mappen[m[1]] ? json(200, { id: m[1], typId: mappen[m[1]].typ, geaendert: '2026-11-09T10:00:00.000Z', werte: mappen[m[1]].werte }) : json(404, { fehler: 'nicht da' });
    if (m && q.methode === 'PUT') {
      if (konflikt) return json(409, { fehler: 'Konflikt' });
      geschrieben[m[1]] = q.body;
      return json(200, { id: m[1] });
    }
    m = /^\/mappen\?sicht=typ:(t-[rp])&von=(\d+)&anzahl=(\d+)$/.exec(q.pfad);
    if (m && q.methode === 'GET') {
      const alle = Object.entries(mappen).filter(([, x]) => x.typ === m[1]).map(([id, x]) => ({ id, typId: x.typ, geaendert: '2026-11-09T10:00:00.000Z', werte: x.werte }));
      m = [null, m[2], m[3]];
      return json(200, { mappen: alle.slice(Number(m[1]), Number(m[1]) + Number(m[2])), gesamt: alle.length });
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = () => 52;
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const e = new TextEncoder().encode(JSON.stringify({ art, id: 'e-1', versuch: 1, erstellt, daten, paket: { id: 'rechnungen', version: '1.0.0' }, einstellungen }));
  const p = inst.exports.dms_puffer(e.length);
  u8().set(e, p);
  const code = inst.exports.dms_ereignis(p, e.length);
  return { code, ergebnis, protokoll, aufrufe, geschrieben, hinweise };
}

let fehler = 0;
function pruefe(name, ok, r) {
  console.log(`${ok ? '✓' : '✗'} ${name}${r?.ergebnis ? `: ${r.ergebnis}` : ''}`);
  if (!ok) { fehler++; console.log(JSON.stringify(r, null, 1).slice(0, 2000)); }
}
const basis = () => ({
  r1: { typ: 't-r', werte: { betrag: E(120.8), datum: '2026-11-01', faellig_am: '2026-11-15' } },
  p1: { typ: 't-p', werte: { rechnung: 'r1', beschreibung: 'Schrauben', menge: 3, einzelpreis: E(12.99) } },
  p2: { typ: 't-p', werte: { rechnung: 'r1', beschreibung: 'Arbeit', gesamtpreis: E(80) } },
});

let r = lauf({ art: 'mappe.angelegt', daten: { mappe: 'r1', typ: 't-r' }, mappen: basis() });
pruefe('Rechnung: Status offen', r.code === 0 && r.geschrieben.r1?.werte.status === 'offen – fällig am 15.11.2026', r);
pruefe('Rechnung: Summenhinweis gesetzt', r.hinweise.r1 === 'Die Positionen ergeben 118,97 €, die Rechnung sagt 120,80 €.', r);

r = lauf({ daten: { mappe: 'p1', typ: 't-p', felder: ['menge'] }, mappen: basis() });
pruefe('Position: Gesamtpreis gefüllt, wenn leer', r.geschrieben.p1?.werte.gesamtpreis?.betrag === 38.97 && !('ust_betrag' in (r.geschrieben.p1?.werte ?? {})), r);
pruefe('Position: Summe der Rechnung geprüft', r.hinweise.r1?.startsWith('Die Positionen ergeben'), r);

const passt = basis(); passt.r1.werte.betrag = E(118.97);
r = lauf({ daten: { mappe: 'r1', typ: 't-r', felder: ['betrag'] }, mappen: passt });
pruefe('Summe passt: Hinweis entfernt', r.hinweise.r1 === null, r);

const netto = basis(); netto.p2.werte.ust_satz = 19;
r = lauf({ daten: { mappe: 'p2', typ: 't-p' }, mappen: netto });
pruefe('Position: Umsatzsteuer netto', r.geschrieben.p2?.werte.ust_betrag?.betrag === 15.2 && !('gesamtpreis' in r.geschrieben.p2.werte), r);

const gut = { g1: { typ: 't-r', werte: { betrag: E(-12.5) } } };
r = lauf({ daten: { mappe: 'g1', typ: 't-r', felder: ['notiz'] }, mappen: gut });
pruefe('Gutschrift: Status in Worten, keine Summenprüfung ohne Betragsänderung', r.geschrieben.g1?.werte.status === 'Gutschrift – noch nicht erhalten' && !('g1' in r.hinweise), r);

r = lauf({ art: 'zeitplan.ausgefuehrt', daten: { datum: '2026-11-20' }, mappen: basis() });
pruefe('Täglich: überfällig und Summen', r.geschrieben.r1?.werte.status === 'überfällig seit 15.11.2026' && typeof r.hinweise.r1 === 'string', r);

r = lauf({ einstellungen: { summenpruefung: false }, daten: { mappe: 'r1', typ: 't-r' }, mappen: basis() });
pruefe('Summenprüfung aus: kein Hinweis', !('r1' in r.hinweise) && r.geschrieben.r1, r);

r = lauf({ daten: { mappe: 'weg', typ: 't-r' }, mappen: {} });
pruefe('Gelöscht: nichts zu tun', r.code === 0, r);

if (fehler) { console.log(`${fehler} Fehler`); process.exit(1); }
console.log('alle Prüfungen bestanden');
