// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung von Ablago: Importe dms.* und WASI,
// Ereignisse mappe.angelegt/geaendert und zeitplan.ausgefuehrt, Mappen mit Werten wie in API v1.
//
//   node tests/modul_test.mjs
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const M = (n) => ({ anzahl: n, einheit: 'monate' });

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher, Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf({ art = 'mappe.geaendert', daten = {}, mappen = {}, konflikt = false, einstellungen = { aktiv: true }, erstellt = '2026-11-10T06:00:00.000Z' }) {
  const aufrufe = [], geschrieben = {}, protokoll = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    if (q.methode === 'GET' && q.pfad === '/typen') return json(200, [{ id: 't-andere', schluessel: 'haushalt:konto' }, { id: 't-vertrag', schluessel: 'vertraege:vertrag' }]);
    let m = /^\/mappen\/([^/?]+)$/.exec(q.pfad);
    if (m && q.methode === 'GET') return mappen[m[1]] ? json(200, { id: m[1], typId: 't-vertrag', geaendert: '2026-11-09T10:00:00.000Z', werte: mappen[m[1]] }) : json(404, { fehler: 'nicht da' });
    if (m && q.methode === 'PUT') {
      if (konflikt) return json(409, { fehler: 'Konflikt' });
      geschrieben[m[1]] = q.body;
      return json(200, { id: m[1] });
    }
    m = /^\/mappen\?sicht=typ:t-vertrag&von=(\d+)&anzahl=(\d+)$/.exec(q.pfad);
    if (m && q.methode === 'GET') {
      const alle = Object.entries(mappen).map(([id, werte]) => ({ id, typId: 't-vertrag', geaendert: '2026-11-09T10:00:00.000Z', werte }));
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
  const e = new TextEncoder().encode(JSON.stringify({ art, id: 'e-1', versuch: 1, erstellt, daten, paket: { id: 'vertraege', version: '1.0.0' }, einstellungen }));
  const p = inst.exports.dms_puffer(e.length);
  u8().set(e, p);
  const code = inst.exports.dms_ereignis(p, e.length);
  return { code, ergebnis, protokoll, aufrufe, geschrieben };
}

let fehler = 0;
function pruefe(name, ok, r) {
  console.log(`${ok ? '✓' : '✗'} ${name}${r?.ergebnis ? `: ${r.ergebnis}` : ''}`);
  if (!ok) { fehler++; console.log(JSON.stringify(r, null, 1).slice(0, 2000)); }
}

const handy = { bezeichnung: 'Handyvertrag Jonas', beginn: '2026-03-15', mindestlaufzeit: M(24), verlaengerung: 'läuft unbefristet weiter',
  kuendigungsfrist: M(1), kuendigung_zum: 'jederzeit', betrag: { betrag: 19.99, waehrung: 'EUR' }, zahlweise: 'monatlich' };

let r = lauf({ art: 'mappe.angelegt', daten: { mappe: 'v1', typ: 't-vertrag' }, mappen: { v1: handy } });
const w = r.geschrieben.v1?.werte ?? {};
pruefe('Neuer Vertrag: berechnet und geschrieben', r.code === 0 && w.kuendigen_bis === '2028-02-14' && w.fruehestes_ende === '2028-03-14'
  && w.status === 'läuft – kündigen bis 14.02.2028, Ende dann 14.03.2028' && w.pro_monat?.betrag === 19.99 && w.pro_monat?.waehrung === 'EUR' && w.laufzeit_monate === 7, r);
pruefe('Mit stand geschrieben', r.geschrieben.v1?.stand === '2026-11-09T10:00:00.000Z', r);
pruefe('Nur berechnete Felder im PUT', Object.keys(w).every((k) => ['status', 'kuendigen_bis', 'fruehestes_ende', 'naechste_verlaengerung', 'ende', 'laufzeit_monate', 'pro_monat'].includes(k)), r);

r = lauf({ daten: { mappe: 'v1', typ: 't-vertrag', felder: ['status', 'kuendigen_bis'] }, mappen: { v1: handy } });
pruefe('Nur berechnete Felder geändert: nichts lesen', r.code === 0 && !r.aufrufe.length, r);

const fertig = { ...handy, status: 'läuft – kündigen bis 14.02.2028, Ende dann 14.03.2028', kuendigen_bis: '2028-02-14', fruehestes_ende: '2028-03-14',
  laufzeit_monate: 7, pro_monat: { betrag: 19.99, waehrung: 'EUR' } };
r = lauf({ daten: { mappe: 'v1', typ: 't-vertrag', felder: ['notiz'] }, mappen: { v1: fertig } });
pruefe('Schon richtig: nichts schreiben', r.code === 0 && !r.aufrufe.some((a) => a.startsWith('PUT')), r);

r = lauf({ daten: { mappe: 'v1', typ: 't-vertrag', felder: ['gekuendigt_am'] }, mappen: { v1: { ...fertig, gekuendigt_am: '2026-11-10' } } });
pruefe('Gekündigt: Kündigen bis wird leer', r.code === 0 && r.geschrieben.v1?.werte.kuendigen_bis === null && r.geschrieben.v1?.werte.ende === '2028-03-14'
  && r.geschrieben.v1?.werte.status === 'gekündigt zum 14.03.2028 – Bestätigung fehlt noch', r);

r = lauf({ konflikt: true, daten: { mappe: 'v1', typ: 't-vertrag' }, mappen: { v1: handy } });
pruefe('409: der Mensch gewinnt, kein Fehler', r.code === 0 && r.ergebnis === 'Vertrag unverändert', r);

r = lauf({ daten: { mappe: 'weg', typ: 't-vertrag' }, mappen: {} });
pruefe('Gelöscht: nichts zu tun', r.code === 0, r);

const viele = {};
for (let i = 0; i < 230; i++) viele[`v${i}`] = { ...handy, beginn: `2025-0${(i % 9) + 1}-01` };
r = lauf({ art: 'zeitplan.ausgefuehrt', daten: { automatisierung: 'a-1', aufgabe: 'taeglich', datum: '2026-11-10' }, mappen: viele });
pruefe('Täglich: alle Verträge in Seiten', r.code === 0 && Object.keys(r.geschrieben).length === 230 && r.aufrufe.includes('GET /typen')
  && r.aufrufe.filter((a) => a.startsWith('GET /mappen?')).length === 3, r);

r = lauf({ art: 'zeitplan.ausgefuehrt', daten: { aufgabe: 'taeglich', datum: '2028-05-20' }, mappen: { v1: fertig } });
pruefe('Täglich: Mindestlaufzeit vorbei → jederzeit kündbar', r.geschrieben.v1?.werte.kuendigen_bis === null
  && r.geschrieben.v1?.werte.status === 'läuft – jederzeit kündbar mit 1 Monat, frühestens zum 20.06.2028', r);

r = lauf({ einstellungen: { aktiv: false }, daten: { mappe: 'v1', typ: 't-vertrag' }, mappen: { v1: handy } });
pruefe('Ausgeschaltet: nichts', r.code === 0 && !r.aufrufe.length, r);

r = lauf({ daten: { mappe: 'v1', typ: 't-vertrag' }, mappen: { v1: { bezeichnung: 'Ohne alles', mindestlaufzeit: 'kaputt', beginn: '31.12.2026' } } });
pruefe('Kaputte Werte: kein Absturz', r.code === 0, r);

if (fehler) { console.log(`${fehler} Fehler`); process.exit(1); }
console.log('alle Prüfungen bestanden');
