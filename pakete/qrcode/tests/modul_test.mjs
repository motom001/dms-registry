// Test des gebauten Moduls (code/modul.wasm) mit einer kleinen Nachbildung des DMS: Importe dms.* und WASI,
// Aktion dms:erkennen wie bei „Aus Dokument ausfüllen“, Seitenbilder (PGM) aus den QR-Matrizen in tests/qr/ –
// auf eine „Visitenkarte“ gesetzt, auch gedreht, verkleinert und verrauscht.
//
//   node tests/modul_test.mjs
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const hier = dirname(fileURLToPath(import.meta.url));
const modul = new WebAssembly.Module(readFileSync(join(hier, '..', 'code', 'modul.wasm')));
const matrix = (name) => readFileSync(join(hier, 'qr', `${name}.txt`), 'utf8').trim().split('\n');

/** Graustufenbild w×h (hell), QR-Codes darauf: { name, x, y, modul (Pixel je Modul), winkel (Grad) }. */
function bild(w, h, codes, rauschen = 0) {
  const px = new Uint8Array(w * h).fill(235);
  let zufall = 7;
  const z = () => { zufall = (zufall * 1103515245 + 12345) & 0x7fffffff; return zufall / 0x7fffffff; };
  for (const c of codes) {
    const m = matrix(c.name), n = m.length, groesse = (n + 8) * c.modul;  // 4 Module Ruhezone ringsum
    const cx = c.x + groesse / 2, cy = c.y + groesse / 2, a = ((c.winkel ?? 0) * Math.PI) / 180, cos = Math.cos(a), sin = Math.sin(a);
    const r = Math.ceil(groesse * 0.75);
    for (let y = Math.max(0, Math.floor(cy - r)); y < Math.min(h, cy + r); y++) {
      for (let x = Math.max(0, Math.floor(cx - r)); x < Math.min(w, cx + r); x++) {
        const dx = x - cx, dy = y - cy;
        const u = (cos * dx + sin * dy + groesse / 2) / c.modul - 4, v = (-sin * dx + cos * dy + groesse / 2) / c.modul - 4;
        if (u < -4 || v < -4 || u >= n + 4 || v >= n + 4) continue;
        const iu = Math.floor(u), iv = Math.floor(v);
        px[y * w + x] = iu >= 0 && iv >= 0 && iu < n && iv < n && m[iv][iu] === '1' ? 25 : 250;
      }
    }
  }
  if (rauschen) for (let i = 0; i < px.length; i++) px[i] = Math.max(0, Math.min(255, px[i] + Math.round((z() - 0.5) * 2 * rauschen)));
  const kopf = new TextEncoder().encode(`P5\n${w} ${h}\n255\n`);
  const aus = new Uint8Array(kopf.length + px.length);
  aus.set(kopf); aus.set(px, kopf.length);
  return aus;
}

// Felder wie bei den Mappentypen Person und Organisation aus dem Paket Basis (nur was die Tests brauchen).
const feld = (title, art, typ = 'text', extra = {}) => ({ title, type: 'object', properties: { wert: typ === 'zahl' ? { type: 'number' } : { type: 'string', ...extra } }, 'x-dms-feldtyp': typ, ...(art ? { 'x-dms-erkennung': art } : {}) });
const PERSON = { type: 'object', properties: {
  vorname: feld('Vorname', 'vorname'), nachname: feld('Nachname', 'nachname'), funktion: feld('Funktion', 'funktion'),
  email: feld('E-Mail', 'email'), telefon: feld('Telefon', 'telefon'), mobil: feld('Mobil', 'mobil'), notiz: feld('Notiz', null),
} };
const ORGANISATION = { type: 'object', properties: {
  name: feld('Name', 'name'), email: feld('E-Mail', 'email'), telefon: feld('Telefon', 'telefon'), fax: feld('Fax', 'fax'),
  internet: feld('Internetseite', 'internet'), strasse: feld('Straße', 'strasse'), hausnummer: feld('Hausnummer', 'hausnummer'),
  plz: feld('PLZ', 'plz', 'zahl'), ort: feld('Ort', 'ort', 'text', { maxLength: 40 }),
} };

/** Ein Aufruf wie im Paket-Läufer: frischer Speicher, Aktion rein, Ergebnis und API-Aufrufe raus. */
function lauf({ seiten, schema = PERSON, dokumente = ['dok-1'], einstellungen = {} }) {
  const aufrufe = [];
  let antwort = new Uint8Array(0), ergebnis = '';
  const protokoll = [];
  const memory = new WebAssembly.Memory({ initial: 256, maximum: 16384 });
  const u8 = () => new Uint8Array(memory.buffer);
  const text = (p, l) => new TextDecoder().decode(u8().subarray(p, p + l));
  const json = (status, x) => { antwort = new TextEncoder().encode(JSON.stringify(x)); return status; };
  const api = (q) => {
    aufrufe.push(`${q.methode} ${q.pfad}`);
    let m;
    if (q.methode === 'GET' && (m = /^\/dokumente\/(dok-\d)\/seiten$/.exec(q.pfad))) return json(200, { id: m[1], anzahl: seiten.length });
    if (q.methode === 'GET' && (m = /^\/dokumente\/dok-\d\/seiten\/(\d+)\/scan\?dpi=\d+$/.exec(q.pfad))) {
      const s = seiten[Number(m[1]) - 1];
      if (!s) return json(404, { fehler: 'keine Seite' });
      antwort = s;
      return 200;
    }
    return json(404, { fehler: `unbekannt: ${q.methode} ${q.pfad}` });
  };
  const dms = {
    api: (p, l) => api(JSON.parse(text(p, l))),
    api_binaer: () => 400, netz: () => -1, datei: () => -1,
    antwort_laenge: () => antwort.length,
    antwort_lesen: (p, max) => { const n = Math.min(max, antwort.length); u8().set(antwort.subarray(0, n), p); return n; },
    speicher_lesen: () => -1, speicher_schreiben: () => 0,
    ergebnis: (p, l) => { ergebnis = text(p, l); return 0; },
    log: (s, p, l) => { protokoll.push(`${s} ${text(p, l)}`); return 0; },
  };
  const dv = () => new DataView(memory.buffer);
  const wasi = {
    fd_write: (fd, iov, n, aus) => { let s = 0; for (let i = 0; i < n; i++) s += dv().getUint32(iov + 8 * i + 4, true); dv().setUint32(aus, s, true); return 0; },
    random_get: (p, l) => { u8().fill(4, p, p + l); return 0; },
    clock_time_get: (_id, _p, aus) => { dv().setBigUint64(aus, BigInt(Date.now()) * 1000000n, true); return 0; },
    environ_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; },
    environ_get: () => 0, args_sizes_get: (a, b) => { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; }, args_get: () => 0,
    proc_exit: (c) => { throw new Error(`proc_exit ${c}`); },
  };
  const importe = { env: { memory }, dms, wasi_snapshot_preview1: {} };
  for (const i of WebAssembly.Module.imports(modul)) {
    if (i.module === 'wasi_snapshot_preview1') importe.wasi_snapshot_preview1[i.name] = wasi[i.name] ?? (() => 52 /* ENOSYS */);
  }
  const inst = new WebAssembly.Instance(modul, importe);
  inst.exports._initialize?.();
  const eingang = new TextEncoder().encode(JSON.stringify({
    aktion: 'dms:erkennen', typ: 'Person', schema, text: 'Text der Texterkennung', dokumente, hinweis: '…', sprache: 'de',
    paket: { id: 'qrcode', version: '1.0.0' }, einstellungen: { dpi: 300, max_seiten: 2, ...einstellungen },
  }));
  const p = inst.exports.dms_puffer(eingang.length);
  u8().set(eingang, p);
  const t0 = Date.now();
  const code = inst.exports.dms_aktion(p, eingang.length);
  let werte = null;
  if (code === 0) werte = Object.fromEntries(Object.entries(JSON.parse(ergebnis).vorschlaege).map(([k, v]) => [k, v.wert]));
  return { code, ergebnis, werte, protokoll, aufrufe, ms: Date.now() - t0 };
}

let fehler = 0;
const sortiert = (o) => o && Object.fromEntries(Object.entries(o).sort(([a], [b]) => a.localeCompare(b)));
function pruefe(name, r, erwartet) {
  if (erwartet.werte) { erwartet = { werte: sortiert(erwartet.werte) }; r = { ...r, werte: sortiert(r.werte) }; }
  const ist = erwartet.werte ? { code: r.code, werte: r.werte } : { code: r.code, ergebnis: r.ergebnis };
  const soll = erwartet.werte ? { code: 0, werte: erwartet.werte } : { code: 1, ergebnis: erwartet.ergebnis };
  const ok = erwartet.werte ? JSON.stringify(ist) === JSON.stringify(soll) : r.code === 1 && soll.ergebnis.test(r.ergebnis);
  if (!ok) { fehler++; console.log(`✗ ${name}: ${r.ergebnis}\n  ist  ${JSON.stringify(ist)}\n  soll ${JSON.stringify(soll, (k, v) => (v instanceof RegExp ? String(v) : v))}\n  ${r.protokoll.join('\n  ')}`); }
  else console.log(`✓ ${name} (${r.ms} ms)`);
}

const karte = (codes, rauschen = 0) => bild(1050, 600, codes, rauschen);  // Visitenkarte 85×55 mm bei 300 dpi (etwa)
const PERSON_30 = { vorname: 'Jonas', nachname: 'Beispiel', funktion: 'Leiter Vertrieb', email: 'jonas.beispiel@example.org', telefon: '+49 30 1234567', mobil: '+49 170 1234567' };

try {
  pruefe('vCard 3.0 → Person', lauf({ seiten: [karte([{ name: 'vcard30', x: 600, y: 120, modul: 4 }])] }), { werte: PERSON_30 });
  pruefe('vCard 3.0 → Organisation (Name aus ORG, Adresse geteilt, PLZ als Zahl)', lauf({ schema: ORGANISATION, seiten: [karte([{ name: 'vcard30', x: 600, y: 120, modul: 4 }])] }),
    { werte: { email: 'jonas.beispiel@example.org', fax: '+49 30 1234568', hausnummer: '12', internet: 'https://musterbau.example', name: 'Musterbau GmbH', ort: 'Musterstadt', plz: 1234, strasse: 'Musterweg', telefon: '+49 30 1234567' } });
  pruefe('vCard 3.0 gedreht, klein und verrauscht', lauf({ seiten: [karte([{ name: 'vcard30', x: 620, y: 150, modul: 3, winkel: 17 }], 40)] }), { werte: PERSON_30 });
  pruefe('vCard 2.1 mit Quoted-Printable und Umlauten', lauf({ schema: ORGANISATION, seiten: [karte([{ name: 'vcard21', x: 600, y: 120, modul: 4 }])] }),
    { werte: { email: 'petra@example.com', hausnummer: '5a', name: 'Beispiel & Söhne KG', ort: 'Beispielhausen', plz: 12345, strasse: 'Hauptstraße', telefon: '030 7654321' } });
  pruefe('vCard 2.1 → Person (Mobil, Name aus N)', lauf({ seiten: [karte([{ name: 'vcard21', x: 600, y: 120, modul: 4 }])] }),
    { werte: { vorname: 'Petra', nachname: 'Müller-Lüdenscheidt', email: 'petra@example.com', telefon: '030 7654321', mobil: '0170 7654321' } });
  pruefe('vCard 4.0 (ROLE, tel:-URI)', lauf({ seiten: [karte([{ name: 'vcard40', x: 600, y: 120, modul: 5 }])] }),
    { werte: { vorname: 'Katrin', nachname: 'Muster', funktion: 'Steuerberaterin', email: 'katrin@kanzlei.example', telefon: '+49-89-555-0100' } });
  pruefe('Visitenkarte auf Seite 2, daneben ein Link-Code', lauf({ seiten: [karte([]), karte([{ name: 'url', x: 80, y: 100, modul: 6 }, { name: 'vcard30', x: 600, y: 120, modul: 4 }])] }), { werte: PERSON_30 });
  pruefe('Präpariert: langer Name gekürzt, Steuerzeichen raus, Foto und leere Zeilen ignoriert', lauf({ schema: ORGANISATION, seiten: [bild(1400, 1000, [{ name: 'lang', x: 300, y: 100, modul: 4 }])] }),
    { werte: { name: 'Sehr lange Firma '.repeat(60).slice(0, 300).trim() } });
  pruefe('Präpariert → Person', lauf({ seiten: [bild(1400, 1000, [{ name: 'lang', x: 300, y: 100, modul: 4 }])] }), { werte: { vorname: 'Jonas', nachname: 'Beispiel' } });
  pruefe('Nur Internetadresse', lauf({ seiten: [karte([{ name: 'url', x: 300, y: 100, modul: 8 }])] }), { ergebnis: /QR-Code gefunden \(Internetadresse\), aber keine Visitenkarte/ });
  pruefe('GiroCode wird nicht ausgewertet', lauf({ seiten: [karte([{ name: 'girocode', x: 300, y: 100, modul: 6 }])] }), { ergebnis: /QR-Code gefunden \(GiroCode\)/ });
  pruefe('Kein QR-Code', lauf({ seiten: [karte([], 20)] }), { ergebnis: /Kein QR-Code gefunden \(1 Seite geprüft\)/ });
  pruefe('Ohne Dokument', lauf({ seiten: [], dokumente: [] }), { ergebnis: /Kein Dokument mitgegeben/ });
  pruefe('Fremde Id wird nicht in den Pfad übernommen', lauf({ seiten: [karte([])], dokumente: ['../typen'] }), { ergebnis: /Kein QR-Code gefunden \(0 Seiten geprüft\)/ });
  const r = lauf({ seiten: [karte([{ name: 'vcard30', x: 600, y: 120, modul: 4 }])] });
  if (r.aufrufe.some((a) => !a.startsWith('GET /dokumente/dok-1/'))) { fehler++; console.log(`✗ nur Seiten gelesen: ${r.aufrufe.join(', ')}`); } else console.log('✓ nur Seiten des mitgegebenen Dokuments gelesen');
  const notiz = JSON.parse(r.ergebnis).vorschlaege;
  if (notiz.notiz || notiz.email?.sicherheit !== 'hoch' || !/^QR-Code \(vCard\): EMAIL/.test(notiz.email?.fundstelle ?? '')) { fehler++; console.log(`✗ Fundstelle/Sicherheit: ${r.ergebnis}`); } else console.log('✓ Feld ohne Art bleibt leer, Fundstelle nennt die vCard-Zeile');
} catch (e) { fehler++; console.log(`✗ Ausnahme: ${e.stack}`); }

if (fehler) { console.log(`${fehler} Prüfung(en) fehlgeschlagen`); process.exit(1); }
console.log('Alle Prüfungen bestanden');
