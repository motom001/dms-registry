// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung von Ablago: Importe dms.* und WASI,
// Ereignis zeitplan.ausgefuehrt, die Schnittstellen aus DMS #1053 (so, wie das Paket sie annimmt), Mappen und Dokumente
// wie in API v1, Speicher des Pakets. Eine „Welt“ bleibt zwischen den Läufen erhalten.
//
//   node tests/modul_test.mjs
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const sha = (t) => createHash('sha256').update(t).digest('hex');

function neueWelt() {
  return {
    freigegeben: new Set(),           // Bereiche mit „Konfiguration lesen“
    nachweiseFrei: false,             // „Nachweise erstellen“ (irgendein Bereich)
    einrichtung: {                    // daten je Bereich
      sicherung: { zeitplan: 'täglich 02:00', ziel: ['NAS im Keller'], verschluesselung: true },
      zugang: { zweifaktor: 'Pflicht', sitzung: '8 Stunden' },
      allgemeines: { version: '0.230', beruflich: true },
    },
    mappen: {}, dokumente: {}, speicher: {}, zaehler: 0,
  };
}

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher, Ereignis rein, Ergebnis und API-Aufrufe raus. */
function lauf(welt, { datum = '2026-11-10', einstellungen = {}, erstellt = `${datum}T04:30:00.000Z`, art = 'zeitplan.ausgefuehrt' } = {}) {
  const aufrufe = [], protokoll = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const memory = new WebAssembly.Memory({ initial: 32, maximum: 4096 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const roh = (status, t) => { antwort = new TextEncoder().encode(t); return status; };
  const json = (status, x) => roh(status, JSON.stringify(x));
  const id = (p) => `${p}-${++welt.zaehler}`;
  const typen = [{ id: 't-verfahren', schluessel: 'compliance_verfahren' }, { id: 't-konf', schluessel: 'compliance_konfiguration' }, { id: 't-nachw', schluessel: 'compliance_nachweise' }];
  const einrichtungText = (b) => JSON.stringify({ bereich: b, ablago: '0.230.0', erstellt: `${datum}T04:30:01.000Z`, daten: welt.einrichtung[b] ?? {} });

  const api = (q, body) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    let m;
    if (q.methode === 'GET' && q.pfad === '/typen') return json(200, typen);
    if ((m = /^\/einrichtung\/([a-z]+)$/.exec(q.pfad)) && q.methode === 'GET') {
      return welt.freigegeben.has(m[1]) ? roh(200, einrichtungText(m[1])) : json(403, { fehler: `Bereich „${m[1]}“ nicht freigegeben` });
    }
    if ((m = /^\/einrichtung\/([a-z]+)\/vergleich$/.exec(q.pfad)) && q.methode === 'POST') {
      // Wie der Kern: ohne Zeitstempel, je geändertem Schlüssel eine Änderung.
      const v = q.body.vorher.daten ?? {}, n = q.body.nachher.daten ?? {};
      const aenderungen = [...new Set([...Object.keys(v), ...Object.keys(n)])].filter((k) => JSON.stringify(v[k]) !== JSON.stringify(n[k]))
        .map((k) => ({ kennung: `${m[1]}.${k}`, vorher: v[k] ?? null, nachher: n[k] ?? null, satz: `${k}: ${JSON.stringify(v[k] ?? '–')} → ${JSON.stringify(n[k] ?? '–')}` }));
      return json(200, { aenderungen });
    }
    if ((m = /^\/nachweise\?monat=(\d{4}-\d{2})$/.exec(q.pfad))) {
      if (!welt.nachweiseFrei) return json(403, { fehler: 'Nachweise nicht freigegeben' });
      return json(200, { monat: m[1], stichtag: `${m[1]}-30`, bereiche: ['sicherung', 'zugang'], benutzer: [{ name: 'Lena' }, { name: 'Jonas' }],
        zahlen: [{ bereich: 'sicherung', name: 'Sicherungsläufe', wert: 30 }, { bereich: 'zugang', name: 'Fehlanmeldungen', wert: 2 }] });
    }
    if ((m = /^\/dokumente\/([^/?]+)\/inhalt$/.exec(q.pfad))) {
      const d = welt.dokumente[m[1]];
      return d ? roh(200, d.versionen.at(-1)) : json(404, { fehler: 'weg' });
    }
    if (q.methode === 'POST' && q.pfad === '/mappen') {
      const w = q.body.werte;
      if (q.body.typId === 't-nachw' && Object.values(welt.mappen).some((x) => x.typId === 't-nachw' && x.werte.monat === w.monat)) return json(422, { fehler: 'Monat schon vorhanden' });
      if (q.body.typId === 't-konf' && Object.values(welt.mappen).some((x) => x.typId === 't-konf' && x.werte.bereich === w.bereich && x.werte.zeitraum === w.zeitraum)) return json(422, { fehler: 'Kennung schon vorhanden' });
      const neu = id('m');
      welt.mappen[neu] = { typId: q.body.typId, werte: { ...w }, dokumente: [] };
      return json(201, { id: neu, typId: q.body.typId, werte: w });
    }
    if ((m = /^\/mappen\?sicht=typ:([^&]+)&von=(\d+)&anzahl=(\d+)$/.exec(q.pfad))) {
      const alle = Object.entries(welt.mappen).filter(([, x]) => x.typId === m[1]).map(([i, x]) => ({ id: i, typId: x.typId, werte: x.werte }));
      return json(200, { mappen: alle.slice(Number(m[2]), Number(m[2]) + Number(m[3])), gesamt: alle.length });
    }
    if ((m = /^\/mappen\/([^/?]+)$/.exec(q.pfad)) && q.methode === 'GET') {
      const x = welt.mappen[m[1]];
      return x ? json(200, { id: m[1], typId: x.typId, werte: x.werte, dokumente: x.dokumente.map((d) => ({ id: d, register: 'dateien', name: welt.dokumente[d]?.name })) }) : json(404, { fehler: 'weg' });
    }
    if ((m = /^\/mappen\/([^/?]+)$/.exec(q.pfad)) && q.methode === 'PUT') {
      const x = welt.mappen[m[1]];
      if (!x) return json(404, { fehler: 'weg' });
      Object.assign(x.werte, q.body.werte);
      return json(200, { id: m[1] });
    }
    if ((m = /^\/mappen\/([^/?]+)\/dokumente\?register=dateien&name=([^&]+)&typ=application%2Fjson$/.exec(q.pfad)) && q.methode === 'POST') {
      const x = welt.mappen[m[1]];
      if (!x || body === undefined) return json(404, { fehler: 'weg' });
      const d = id('d');
      welt.dokumente[d] = { mappe: m[1], name: m[2], versionen: [body] };
      x.dokumente.push(d);
      return json(201, { dokument: { id: d, name: m[2] } });
    }
    if ((m = /^\/dokumente\/([^/?]+)\/ersetzen\?typ=application%2Fjson$/.exec(q.pfad)) && q.methode === 'POST') {
      const d = welt.dokumente[m[1]];
      if (!d || body === undefined) return json(404, { fehler: 'weg' });
      d.versionen.push(body);
      return json(201, { id: m[1] });
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    api_binaer: (p, l, b, bl) => api(JSON.parse(text(p, l)), text(b, bl)),
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    speicher_lesen: (p, l) => { const k = text(p, l); if (!(k in welt.speicher)) return -1; antwort = new TextEncoder().encode(welt.speicher[k]); return antwort.length; },
    speicher_schreiben: (p, l, w, wl) => { welt.speicher[text(p, l)] = text(w, wl); return 0; },
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = () => 52;
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const e = new TextEncoder().encode(JSON.stringify({ art, id: 'e-1', versuch: 1, erstellt, daten: { automatisierung: 'a-1', aufgabe: 'taeglich', datum },
    paket: { id: 'compliance', version: '1.0.0' }, einstellungen }));
  const p = inst.exports.dms_puffer(e.length);
  u8().set(e, p);
  const code = inst.exports.dms_ereignis(p, e.length);
  return { code, ergebnis, protokoll, aufrufe };
}

let fehler = 0;
function pruefe(name, ok, r) {
  console.log(`${ok ? '✓' : '✗'} ${name}${r?.ergebnis ? `: ${r.ergebnis}` : ''}`);
  if (!ok) { fehler++; console.log(JSON.stringify(r, null, 1).slice(0, 3000)); }
}
const konf = (welt) => Object.entries(welt.mappen).filter(([, x]) => x.typId === 't-konf');
const nachw = (welt) => Object.entries(welt.mappen).filter(([, x]) => x.typId === 't-nachw');
const von = (welt, bereich) => konf(welt).filter(([, x]) => x.werte.bereich === bereich);

// 1. Nichts freigegeben (Vorgabe nach der Installation)
const welt = neueWelt();
let r = lauf(welt, { art: 'paket.einstellungen_geaendert' });
pruefe('Nichts freigegeben: nichts angelegt, Hinweis', r.code === 0 && !konf(welt).length && r.ergebnis.startsWith('Noch kein Bereich freigegeben'), r);

// 2. Erstlauf: Sicherung und Zugang angehakt
welt.freigegeben = new Set(['sicherung', 'zugang']);
r = lauf(welt, { art: 'paket.einstellungen_geaendert' });
let [sid, s] = von(welt, 'Sicherung')[0] ?? [];
pruefe('Erstlauf: je Bereich eine Monatsmappe', r.code === 0 && konf(welt).length === 2 && s?.werte.zeitraum === '2026-11' && s.werte.status === 'aktuell'
  && s.werte.aenderung.startsWith('Erster Stand') && s.werte.versionen === 1 && s.werte.ablago_version === '0.230.0', r);
const dok = s ? welt.dokumente[s.dokumente[0]] : null;
pruefe('Erstlauf: JSON-Datei mit Prüfwert', dok?.name === 'konfiguration-sicherung-2026-11.json' && s.werte.pruefwert === sha(dok.versionen[0]), r);
pruefe('Kennung entsteht im Kern (nicht vom Paket gesetzt)', s && !('kennung' in s.werte), r);

// 3. Am nächsten Tag unverändert
r = lauf(welt, { datum: '2026-11-11' });
pruefe('Unverändert: nichts Neues', r.code === 0 && konf(welt).length === 2 && dok.versionen.length === 1 && r.ergebnis.includes('2 Bereiche unverändert'), r);

// 4. Zeitplan der Sicherung geändert – zählt: neue Version im selben Monat
welt.einrichtung.sicherung.zeitplan = 'täglich 03:00';
r = lauf(welt, { datum: '2026-11-12' });
pruefe('Änderung, die zählt: neue Version', r.code === 0 && konf(welt).length === 2 && dok.versionen.length === 2 && s.werte.versionen === 2
  && s.werte.aenderung.includes('zeitplan') && s.werte.stand_vom === '2026-11-12' && s.werte.pruefwert === sha(dok.versionen[1]), r);

// 5. Sitzungsdauer geändert – zählt nicht (nicht vorausgewählt)
welt.einrichtung.zugang.sitzung = '4 Stunden';
const [, z] = von(welt, 'Zugang und Berechtigungen')[0];
r = lauf(welt, { datum: '2026-11-13' });
pruefe('Änderung, die nicht zählt: nichts', r.code === 0 && z.werte.versionen === 1 && welt.dokumente[z.dokumente[0]].versionen.length === 1, r);
r = lauf(welt, { datum: '2026-11-14', einstellungen: { zaehlt_zugang: ['Sitzungsdauer'] } });
pruefe('Danach angehakt: zählt beim nächsten echten Unterschied (Grundlage bleibt der letzte Stand)', r.code === 0 && z.werte.versionen === 2 && z.werte.aenderung.includes('sitzung'), r);

// 6. Neuer Monat mit Änderung: neue Mappe, Vormonat abgelöst; Nachweise des Vormonats (noch nicht freigegeben)
welt.einrichtung.sicherung.ziel = ['NAS im Keller', 'Cloud (example.org)'];
r = lauf(welt, { datum: '2026-12-01' });
const neu = von(welt, 'Sicherung').find(([, x]) => x.werte.zeitraum === '2026-12');
pruefe('Neuer Monat: neue Mappe mit Vorgänger', r.code === 0 && neu && neu[1].werte.vorgaenger === sid && neu[1].werte.status === 'aktuell', r);
pruefe('Vormonat abgelöst', s.werte.status === 'abgelöst' && s.werte.abgeloest_am === '2026-12-01' && s.werte.nachfolger === neu?.[0], r);
pruefe('Nachweise ohne Freigabe: keine', !nachw(welt).length, r);

// 7. Nachweise freigegeben – der Lauf holt November nach, der Dezember kommt erst im Januar
welt.nachweiseFrei = true;
r = lauf(welt, { datum: '2026-12-02' });
let n = nachw(welt);
pruefe('Nachweise November nachgeholt', r.code === 0 && n.length === 1 && n[0][1].werte.monat === '2026-11' && n[0][1].werte.benutzer === 2
  && n[0][1].werte.zusammenfassung === 'Zugang und Berechtigungen: Fehlanmeldungen 2\nSicherung: Sicherungsläufe 30'
  && n[0][1].werte.bereiche === 'Zugang und Berechtigungen, Sicherung' && welt.dokumente[n[0][1].dokumente[0]]?.name === 'nachweise-2026-11.json', r);
r = lauf(welt, { datum: '2026-12-03' });
pruefe('Nachweise nicht doppelt', nachw(welt).length === 1, r);
r = lauf(welt, { datum: '2027-02-05' });
n = nachw(welt).map(([, x]) => x.werte.monat).sort();
pruefe('Verpasste Monate nachgeholt', JSON.stringify(n) === '["2026-11","2026-12","2027-01"]' && r.ergebnis.includes('nachgeholt'), r);

// 8. Auswahl „was zählt“ geändert – zählt im Bereich Allgemeines, sobald er freigegeben ist
const w2 = neueWelt();
w2.freigegeben = new Set(['allgemeines']);
lauf(w2, {});
r = lauf(w2, { datum: '2026-11-11', einstellungen: { zaehlt_ablage: ['Hilfetext'] } });
const [, allg] = von(w2, 'Allgemeines')[0];
pruefe('Geänderte Auswahl: neue Version in Allgemeines', r.code === 0 && allg.werte.versionen === 2 && allg.werte.aenderung.includes('Was zählt: neu „Hilfetext“ (Ablage)'), r);
r = lauf(w2, { datum: '2026-11-12', einstellungen: { zaehlt_ablage: ['Hilfetext'], zaehlt_allgemeines: [] } });
pruefe('Auswahl ohne „Auswahl in diesen Einstellungen“: zählt nicht', allg.werte.versionen === 2, r);

// 9. Speicher verloren und Dokument weg: kein Absturz, neuer Ausgangsstand
const w3 = neueWelt();
w3.freigegeben = new Set(['sicherung']);
lauf(w3, {});
w3.dokumente = {};
w3.einrichtung.sicherung.zeitplan = 'stündlich';
r = lauf(w3, { datum: '2026-11-11' });
pruefe('Vorheriger Stand nicht lesbar: neuer Ausgangsstand in der Mappe des Monats', r.code === 0 && konf(w3).length === 1
  && konf(w3)[0][1].werte.aenderung.includes('Neuer Ausgangsstand') && konf(w3)[0][1].werte.versionen === 2 && konf(w3)[0][1].dokumente.length === 2, r);
for (const d of konf(w3)[0][1].dokumente) delete w3.dokumente[d];  // mit der Mappe verschwinden ihre Dokumente
delete w3.mappen[konf(w3)[0][0]];
w3.einrichtung.sicherung.zeitplan = 'täglich 01:00';
r = lauf(w3, { datum: '2026-11-11' });
pruefe('Auch die Mappe weg: neue Mappe', r.code === 0 && konf(w3).length === 1 && konf(w3)[0][1].werte.versionen === 1, r);
w3.speicher = { stand: 'kaputt{' };
r = lauf(w3, { datum: '2026-11-12' });
pruefe('Kaputter Speicher: aktuellen Stand wiedergefunden, keine zweite Mappe', r.code === 0 && konf(w3).length === 1 && r.aufrufe.some((a) => a.startsWith('GET /mappen?sicht=typ:t-konf')), r);

// 10. Keine Netzaufrufe, keine fremden Pfade
pruefe('Nur bekannte Pfade', !r.aufrufe.some((a) => a.includes('unbekannt')), r);

if (fehler) { console.log(`${fehler} Fehler`); process.exit(1); }
console.log('alle Prüfungen bestanden');
