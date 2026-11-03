// Sammeldatei im Browser (motom001/dms#461): wie werkzeuge/sammeldatei.py – Auswahl samt Abhängigkeiten,
// passend zur DMS-Version; jedes Archiv gegen katalog.json geprüft; ZIP mit sammeldatei.json, LIESMICH.txt,
// dem signierten Katalog (katalog.json und katalog.sig Byte für Byte, #74) und den Archiven unter pakete/.
// Es wird nichts hochgeladen; die Datei entsteht nur in diesem Browser. Die DMS-Version kommt aus dms.js
// (Fragment #dms=…, gemerkt nur in diesem Browser) – die Adresse liest diese Seite selbst nicht.
(function () {
  var VORAUSWAHL = ['texterkennung'];
  var KATALOG_URL = 'https://catalog.ablago.app/katalog.json';
  var BEREICH = /^(>=|>|=|\^|~)?(\d+\.\d+\.\d+)( <(\d+\.\d+\.\d+))?$/;
  var VERSION = /^\d+\.\d+\.\d+$/;
  var katalog = null, katalogRoh = null, signatur = null, gewaehlt = [];
  function teile(v) { return v.split('.').map(function (x) { return parseInt(x, 10) || 0; }); }
  function vergleiche(a, b) { var x = teile(a), y = teile(b); for (var i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] - y[i]; return 0; }
  function passt(v, bereich) {
    var m = BEREICH.exec((bereich || '').trim()); if (!m) return false;
    var op = m[1] || '=', basis = m[2], ober = m[4], c = vergleiche(v, basis), b = teile(basis), ok;
    if (op === '>=') ok = c >= 0; else if (op === '>') ok = c > 0;
    else if (op === '^') ok = c >= 0 && (b[0] > 0 ? vergleiche(v, (b[0] + 1) + '.0.0') < 0 : vergleiche(v, '0.' + (b[1] + 1) + '.0') < 0);
    else if (op === '~') ok = c >= 0 && vergleiche(v, b[0] + '.' + (b[1] + 1) + '.0') < 0;
    else ok = c === 0;
    return ok && (!ober || vergleiche(v, ober) < 0);
  }
  function dmsPasst(dms, bereich) { return !dms || passt(dms, bereich); }
  function paket(id) { return katalog.pakete.filter(function (p) { return p.id === id; })[0]; }
  function neueste(p, bereich, dms) {
    return p.versionen.slice().sort(function (a, b) { return vergleiche(b.version, a.version); })
      .filter(function (v) { return (!bereich || passt(v.version, bereich)) && dmsPasst(dms, v.dms); })[0];
  }
  // Wie auswahlMitAbhaengigkeiten im DMS: neueste passende Version, Abhängigkeiten mit, Abhängigkeiten zuerst.
  function plane(ids, dms) {
    var plan = {}, reihe = [], probleme = [];
    function name(id) { var p = paket(id); return p ? p.name : id; }
    function nimm(id, bereich, von) {
      if (plan[id]) {
        if (!von) plan[id].gewaehlt = true;
        else { if (plan[id].fuer.indexOf(von) < 0) plan[id].fuer.push(von); if (bereich && !passt(plan[id].v.version, bereich)) probleme.push('„' + name(von) + '“ braucht „' + plan[id].name + '“ ' + bereich + ', gewählt ist ' + plan[id].v.version + '.'); }
        return;
      }
      var p = paket(id);
      if (!p) { probleme.push('„' + name(von) + '“ braucht „' + id + '“ – das gibt es im Katalog nicht.'); return; }
      var v = neueste(p, bereich, dms);
      if (!v) { probleme.push(von ? '„' + name(von) + '“ braucht „' + p.name + '“ ' + bereich + '; dazu passt keine Version für Ablago ' + dms + '.' : '„' + p.name + '“: keine Version passt zu DMS ' + dms + '.'); return; }
      plan[id] = { id: id, name: p.name, v: v, gewaehlt: !von, fuer: von ? [von] : [] };
      Object.keys(v.abhaengigkeiten || {}).forEach(function (a) { nimm(a, v.abhaengigkeiten[a], id); });
    }
    ids.forEach(function (id) { nimm(id, null, null); });
    var fertig = {}, unterwegs = {};
    function besuche(id) {
      if (fertig[id]) return true; if (unterwegs[id]) return false; unterwegs[id] = true;
      var ok = Object.keys(plan[id].v.abhaengigkeiten || {}).every(function (a) { return !plan[a] || besuche(a); });
      if (!ok) return false; delete unterwegs[id]; fertig[id] = true; reihe.push(plan[id]); return true;
    }
    if (!Object.keys(plan).every(besuche)) probleme.push('Die Abhängigkeiten bilden einen Kreis.');
    return { pakete: reihe, probleme: probleme, plan: plan };
  }
  function el(tag, attr, kinder) {
    var e = document.createElement(tag);
    Object.keys(attr || {}).forEach(function (k) { if (k === 'text') e.textContent = attr[k]; else if (k === 'className') e.className = attr[k]; else e.setAttribute(k, attr[k]); });
    (kinder || []).forEach(function (k) { if (k) e.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); });
    return e;
  }
  function dmsVersion() { var w = document.getElementById('dms-version').value.trim(); return VERSION.test(w) ? w : null; }
  function zeichne() {
    // Gewählte Pakete ohne passende Version für diese DMS-Version zählen nicht (die Wahl bleibt für eine andere Version).
    var dms = dmsVersion(), wirksam = gewaehlt.filter(function (id) { return neueste(paket(id), null, dms); });
    var r = plane(wirksam, dms), liste = document.getElementById('sammel-liste');
    liste.textContent = '';
    katalog.pakete.slice().sort(function (a, b) { return (VORAUSWAHL.indexOf(b.id) >= 0) - (VORAUSWAHL.indexOf(a.id) >= 0) || a.name.localeCompare(b.name, 'de'); }).forEach(function (p) {
      var v = neueste(p, null, dms), im = r.plan[p.id], mit = im && !im.gewaehlt, an = wirksam.indexOf(p.id) >= 0 || mit;
      var box = el('input', { type: 'checkbox', id: 'p-' + p.id });
      box.checked = an; box.disabled = !v || mit;
      box.addEventListener('change', function () { document.getElementById('sammel-ergebnis').textContent = ''; if (box.checked) gewaehlt.push(p.id); else gewaehlt = gewaehlt.filter(function (x) { return x !== p.id; }); zeichne(); });
      var zeige = (im && im.v) || v || p.versionen[0];
      var unter = !v ? 'Braucht Ablago ' + p.versionen[0].dms + (dms ? ' – du hast ' + dms + '.' : '.') : (zeige.code ? 'Enthält Code – die Rechte bestätigst du in Ablago für dieses Paket einzeln.' : 'Kein Code – legt Mappentypen und Ansichten an.');
      var empfohlen = VORAUSWAHL.indexOf(p.id) >= 0 && v;
      liste.appendChild(el('li', { className: an ? 'an' : '' }, [el('label', { for: 'p-' + p.id }, [box, el('span', {}, [
        el('strong', { text: p.name }), ' ', el('span', { className: 'leise', text: zeige.version }),
        mit ? ' ' : null, mit ? el('span', { className: 'marke-mit', text: 'kommt mit – gebraucht von ' + im.fuer.map(function (f) { return r.plan[f] ? r.plan[f].name : f; }).join(', ') }) : null,
        empfohlen ? ' ' : null, empfohlen ? el('span', { className: 'marke-mit', text: 'empfohlen' }) : null,
        el('span', { className: 'unter', text: p.beschreibung }), el('span', { className: 'unter', text: unter }),
      ])])]));
    });
    var pr = document.getElementById('sammel-probleme');
    pr.hidden = !r.probleme.length; pr.textContent = '';
    if (r.probleme.length) pr.appendChild(el('ul', {}, r.probleme.map(function (x) { return el('li', { text: x }); })));
    var groesse = r.pakete.reduce(function (n, x) { return n + x.v.groesse; }, 0);
    document.getElementById('sammel-zusammenfassung').textContent = r.pakete.length ? r.pakete.length + (r.pakete.length === 1 ? ' Paket' : ' Pakete') + ', etwa ' + (groesse / 1048576).toFixed(1).replace('.', ',') + ' MB' : 'Noch nichts gewählt.';
    document.getElementById('sammel-los').disabled = !r.pakete.length || r.probleme.length > 0;
    return r;
  }
  // ---- ZIP (gespeichert, ohne Kompression; die Archive sind schon komprimiert) ----
  var CRC = (function () { var t = new Uint32Array(256); for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(b) { var c = 0xffffffff; for (var i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }
  function zip(dateien) {
    var teile = [], zentral = [], versatz = 0, enc = new TextEncoder();
    dateien.forEach(function (d) {
      var name = enc.encode(d.name), crc = crc32(d.daten), n = d.daten.length;
      var k = new DataView(new ArrayBuffer(30));
      k.setUint32(0, 0x04034b50, true); k.setUint16(4, 20, true); k.setUint16(6, 0x0800, true); k.setUint16(8, 0, true);
      k.setUint16(10, 0, true); k.setUint16(12, 33, true); k.setUint32(14, crc, true); k.setUint32(18, n, true); k.setUint32(22, n, true);
      k.setUint16(26, name.length, true); k.setUint16(28, 0, true);
      var z = new DataView(new ArrayBuffer(46));
      z.setUint32(0, 0x02014b50, true); z.setUint16(4, 20, true); z.setUint16(6, 20, true); z.setUint16(8, 0x0800, true); z.setUint16(10, 0, true);
      z.setUint16(12, 0, true); z.setUint16(14, 33, true); z.setUint32(16, crc, true); z.setUint32(20, n, true); z.setUint32(24, n, true);
      z.setUint16(28, name.length, true); z.setUint32(42, versatz, true);
      teile.push(k.buffer, name, d.daten); zentral.push(z.buffer, name);
      versatz += 30 + name.length + n;
    });
    var groesse = zentral.reduce(function (s, x) { return s + x.byteLength; }, 0);
    var e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, dateien.length, true); e.setUint16(10, dateien.length, true); e.setUint32(12, groesse, true); e.setUint32(16, versatz, true);
    return new Blob(teile.concat(zentral, [e.buffer]), { type: 'application/zip' });
  }
  function hex(buf) { return Array.prototype.map.call(new Uint8Array(buf), function (x) { return ('0' + x.toString(16)).slice(-2); }).join(''); }
  var LIESMICH = 'Sammeldatei für Ablago\n=======================\n\nDiese Datei enthält mehrere Pakete aus dem Paketkatalog des Ablago-Projekts\n(https://catalog.ablago.app/) – für Ablago ohne Internet.\n\nSo installierst du sie:\n  Werkbank → Pakete → „Ohne Internet …“ → Sammeldatei wählen\n  (oder im Einrichtungsassistenten, Schritt „Pakete dazuholen“).\n\nAblago prüft vorher jedes Paket gegen die Prüfsumme in sammeldatei.json und\ninstalliert dann Paket für Paket; Rechte von Paketen mit Code bestätigst du einzeln.\nEntpacken musst du nichts.\n';
  async function herunterladen(ev) {
    ev.preventDefault();
    var r = zeichne(), aus = document.getElementById('sammel-ergebnis'), knopf = document.getElementById('sammel-los');
    if (!r.pakete.length || r.probleme.length) return;
    if (!window.crypto || !crypto.subtle) { aus.textContent = 'Dein Browser kann hier keine Prüfsummen berechnen (nur über https).'; return; }
    knopf.disabled = true; aus.textContent = 'Lade und prüfe die Pakete …';
    try {
      var dateien = [], eintraege = [];
      for (var i = 0; i < r.pakete.length; i++) {
        var x = r.pakete[i], antwort = await fetch(x.v.archiv, { cache: 'no-store' });
        if (!antwort.ok) throw new Error(x.v.archiv + ': ' + antwort.status);
        var daten = new Uint8Array(await antwort.arrayBuffer());
        if (daten.length !== x.v.groesse || hex(await crypto.subtle.digest('SHA-256', daten)) !== x.v.sha256) throw new Error(x.name + ' ' + x.v.version + ': Prüfsumme passt nicht zum Katalog – abgebrochen.');
        var name = 'pakete/' + x.id + '-' + x.v.version + '.zip';
        dateien.push({ name: name, daten: daten });
        eintraege.push({ id: x.id, version: x.v.version, name: x.name, archiv: name, sha256: x.v.sha256, groesse: x.v.groesse, gewaehlt: x.gewaehlt });
      }
      var jetzt = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      var vz = { format: 1, art: 'dms-sammeldatei', erstellt: jetzt, quelle: katalog.quelle || 'https://github.com/motom001/dms-registry', katalog: KATALOG_URL, dms: dmsVersion(), pakete: eintraege };
      var enc = new TextEncoder();
      // Signierter Katalog (#74): genau die geladenen Bytes – die Signatur gilt nur für sie.
      var mitKatalog = signatur ? [{ name: 'katalog.json', daten: katalogRoh }, { name: 'katalog.sig', daten: signatur }] : [];
      var blob = zip([{ name: 'sammeldatei.json', daten: enc.encode(JSON.stringify(vz, null, 2) + '\n') }, { name: 'LIESMICH.txt', daten: enc.encode(LIESMICH) }].concat(mitKatalog, dateien));
      var summe = hex(await crypto.subtle.digest('SHA-256', await blob.arrayBuffer()));
      var dateiname = 'dms-pakete-' + jetzt.slice(0, 10) + '.zip';
      var a = el('a', { href: URL.createObjectURL(blob), download: dateiname, className: 'knopf' }, ['Noch einmal speichern']);
      aus.textContent = '';
      aus.appendChild(el('p', {}, [el('strong', { text: dateiname }), ' mit ' + eintraege.map(function (e) { return e.name + ' ' + e.version; }).join(', ') + ' (' + (blob.size / 1048576).toFixed(1).replace('.', ',') + ' MB).']));
      aus.appendChild(el('p', { className: 'leise' }, ['SHA-256 der Datei: ', el('code', { text: summe }), ' – Ablago zeigt denselben Wert nach dem Hochladen.']));
      aus.appendChild(a);
      a.click();
    } catch (e) { aus.textContent = 'Das hat nicht geklappt: ' + e.message; }
    finally { knopf.disabled = false; zeichne(); }
  }
  async function start() {
    var form = document.getElementById('sammel');
    if (!form) return;
    try {
      // Erst die Signatur, dann den Katalog: Wird dazwischen neu veröffentlicht, passt die Signatur nicht, und das DMS fragt nach der Herkunft.
      var s = await fetch('katalog.sig', { cache: 'no-store' }).catch(function () { return null; });
      signatur = s && s.ok ? new Uint8Array(await s.arrayBuffer()) : null;
      var k = await fetch('katalog.json', { cache: 'no-store' });
      if (!k.ok) throw new Error(String(k.status));
      katalogRoh = new Uint8Array(await k.arrayBuffer());
      katalog = JSON.parse(new TextDecoder().decode(katalogRoh));
    }
    catch (e) { document.getElementById('sammel-laden').textContent = 'Der Katalog lässt sich nicht laden: ' + e.message; return; }
    var gemerkt = window.dmsVersion ? window.dmsVersion.lies() : '', feld = document.getElementById('dms-version');
    if (gemerkt) feld.value = gemerkt;
    else {
      // Vorgabe: die neueste DMS-Version (Releases auf GitHub); klappt das nicht, bleibt das Feld leer.
      fetch('https://api.github.com/repos/motom001/dms/releases/latest').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
        var v = j && String(j.tag_name || '').replace(/^v/, '');
        if (v && VERSION.test(v) && !feld.value) { feld.value = v; zeichne(); }
      }).catch(function () {});
    }
    gewaehlt = VORAUSWAHL.filter(function (id) { return paket(id); });
    feld.addEventListener('input', function () {
      // Wie die Übersicht: eine gültige (oder leere) Eingabe merkt sich der Browser für die anderen Katalogseiten.
      var w = feld.value.trim(); if (window.dmsVersion && (!w || VERSION.test(w))) window.dmsVersion.merke(w);
      document.getElementById('sammel-ergebnis').textContent = ''; zeichne();
    });
    form.addEventListener('submit', herunterladen);
    document.getElementById('sammel-laden').hidden = true;
    form.hidden = false;
    zeichne();
  }
  start();
})();
