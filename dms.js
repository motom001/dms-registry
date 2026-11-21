// Katalog-Webseite der DMS-Registry: Suche/Filter und „In meinem DMS installieren“.
// Die Adresse des eigenen DMS bleibt nur in diesem Browser (localStorage).
// Sprung auf einen Mappentyp (#typ-…, #115): Bereich und Zeile aufklappen, damit man ihn sieht.
(function () {
  function oeffne() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (id.indexOf('typ-') !== 0) return;
    var z = document.getElementById(id);
    for (var x = z; x; x = x.parentElement) if (x.tagName === 'DETAILS') x.open = true;
    if (z) z.scrollIntoView();
  }
  window.addEventListener('hashchange', oeffne);
  document.addEventListener('DOMContentLoaded', oeffne);
})();
(function () {
  var SCHLUESSEL = 'dms-adresse';
  function lies() { try { return localStorage.getItem(SCHLUESSEL) || ''; } catch (e) { return ''; } }
  function merke(a) { try { localStorage.setItem(SCHLUESSEL, a); } catch (e) { /* nur jetzt */ } }
  function gueltig(a) { try { var u = new URL(a); return (u.protocol === 'http:' || u.protocol === 'https:') && !!u.host; } catch (e) { return false; } }
  function frage(danach) {
    var d = document.getElementById('dms-dialog'), i = document.getElementById('dms-url'), f = document.getElementById('dms-fehler');
    i.value = lies(); f.hidden = true;
    d.onclose = function () {
      if (d.returnValue !== 'ok') return;
      var a = i.value.trim().replace(/\/+$/, '');
      if (!gueltig(a)) { f.hidden = false; d.showModal(); return; }
      merke(a); if (danach) danach(a);
    };
    d.showModal();
  }
  function oeffne(was) {
    var los = function (a) { location.href = a + '/werkbank/pakete?installieren=' + encodeURIComponent(was); };
    var a = lies();
    if (gueltig(a)) los(a); else frage(los);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-installieren]');
    if (b) { e.preventDefault(); oeffne(b.getAttribute('data-installieren')); return; }
    if (e.target.closest('[data-dms-adresse]')) { e.preventDefault(); frage(null); }
  });
  // Passt das Paket zu meinem DMS? (#84) Die Version kommt aus dem Fragment #dms=… (Link aus dem DMS,
  // motom001/dms#622) oder wird eingetippt – sie bleibt nur in diesem Browser und geht an keinen Server.
  var BEREICH = /^(>=|>|=|\^|~)?(\d+\.\d+\.\d+)( <(\d+\.\d+\.\d+))?$/, VERSION = /^\d+\.\d+\.\d+$/, VSCHL = 'dms-version';
  var EN = document.documentElement.lang === 'en';
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
  function mindestens(bereich) { var m = BEREICH.exec((bereich || '').trim()); return m ? m[2] : bereich; }
  function liesVersion() { try { var v = localStorage.getItem(VSCHL) || ''; return VERSION.test(v) ? v : ''; } catch (e) { return ''; } }
  function merkeVersion(v) { try { if (v) localStorage.setItem(VSCHL, v); else localStorage.removeItem(VSCHL); } catch (e) { /* nur jetzt */ } }
  (function ausFragment() {
    var m = /(?:^#|&)dms=(\d+\.\d+\.\d+)(?:&|$)/.exec(location.hash);
    if (!m) return;
    merkeVersion(m[1]);
    // Fragment wieder entfernen, damit die Version nicht mit einem geteilten Link weitergegeben wird.
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* egal */ }
  })();
  // Für sammeldatei.js (läuft nach dms.js): dieselbe gemerkte Version, kein zweites Lesen der Adresse.
  window.dmsVersion = { lies: liesVersion, merke: merkeVersion };
  // Ergebnis je Paket: ja (neueste Version passt) · aelter (eine ältere passt) · nein; null ohne Version.
  function pruefe(versionen, dms) {
    if (!dms) return null;
    if (passt(dms, versionen[0][1])) return { fall: 'ja', version: versionen[0][0] };
    for (var i = 1; i < versionen.length; i++) if (passt(dms, versionen[i][1])) return { fall: 'aelter', version: versionen[i][0], neu: versionen[0] };
    return { fall: 'nein', neu: versionen[0] };
  }
  function marke(r) {
    if (!r) return '';
    if (r.fall === 'ja') return EN ? 'fits your Ablago' : 'passt zu deinem Ablago';
    if (r.fall === 'aelter') return EN ? 'Ablago update recommended' : 'Ablago-Update empfohlen';
    return (EN ? 'needs Ablago ' : 'braucht Ablago ') + mindestens(r.neu[1]) + (EN ? '+' : ' oder neuer');
  }
  var suche = document.getElementById('suche'), art = document.getElementById('art'), kat = document.getElementById('kategorie'),
      autor = document.getElementById('autor'), vfeld = document.getElementById('dms-version'), nur = document.getElementById('nur-passend'),
      lokal = document.getElementById('nur-lokal');
  function filtern() {
    var q = (suche.value || '').trim().toLowerCase(), a = art.value, k = kat ? kat.value : '', au = autor ? autor.value : '', n = 0;
    var dms = vfeld && VERSION.test(vfeld.value.trim()) ? vfeld.value.trim() : '';
    if (nur) { nur.disabled = !dms; if (!dms) nur.checked = false; }
    document.querySelectorAll('.kachel').forEach(function (el) {
      var r = el.dataset.versionen ? pruefe(JSON.parse(el.dataset.versionen), dms) : null, m = el.querySelector('.passt-marke');
      if (m) { m.hidden = !r; m.textContent = marke(r); m.className = 'passt-marke' + (r ? ' ' + r.fall : ''); el.classList.toggle('mit-marke', !!r); }
      // Sprachen und Ergänzungen (#165) nur mit Suche oder passendem Filter „Paketart“.
      var gefiltert = !!(q || a || k || au || (nur && nur.checked) || (lokal && lokal.checked));
      var sichtbar = (!el.dataset.versteckt || !!q || a === el.dataset.art) && (!el.dataset.anfang || gefiltert);
      var ok = sichtbar && (!q || el.dataset.suche.indexOf(q) >= 0) && (!a || el.dataset.art === a)
        && (!k || (' ' + el.dataset.kategorien + ' ').indexOf(' ' + k + ' ') >= 0) && (!au || el.dataset.autor === au)
        && (!(nur && nur.checked) || (r && r.fall === 'ja')) && (!(lokal && lokal.checked) || el.dataset.netz === 'lokal');
      el.hidden = !ok; if (ok && el.closest('#alle')) n++;
    });
    // „Für den Anfang“ nur ohne Suche und Filter – sonst stünden Treffer doppelt da.
    var anfang = document.getElementById('anfang'), gefiltert = !!(q || a || k || au || (nur && nur.checked) || (lokal && lokal.checked));
    var mitAnfang = anfang && !!anfang.querySelector('.kachel');
    if (mitAnfang) anfang.hidden = gefiltert;
    var at = document.getElementById('alle-text'); if (at) at.hidden = gefiltert;
    var titel = document.getElementById('alle-titel'); if (titel) titel.textContent = mitAnfang && !gefiltert ? titel.dataset.weitere : titel.dataset.alle;
    document.getElementById('keine').hidden = n > 0;
    // Kategorie und Autor stehen in der Adresse (teilbar, Zurück im Browser); die DMS-Version nie.
    var p = new URLSearchParams(location.search);
    if (k) p.set('kategorie', k); else p.delete('kategorie');
    if (au) p.set('autor', au); else p.delete('autor');
    if (a) p.set('art', a); else p.delete('art');
    var ziel = location.pathname + (p.toString() ? '?' + p.toString() : '');
    if (ziel !== location.pathname + location.search) { try { history.replaceState(null, '', ziel); } catch (e) { /* egal */ } }
  }
  if (suche) {
    var p = new URLSearchParams(location.search);
    if (kat && p.get('kategorie')) kat.value = p.get('kategorie');
    if (autor && p.get('autor')) autor.value = p.get('autor');
    if (art && p.get('art')) art.value = p.get('art');
    // Kacheln oder Liste (#165): bleibt nur in diesem Browser.
    var ANSICHT = 'katalog-ansicht';
    function ansicht(w) {
      document.querySelectorAll('.kacheln').forEach(function (x) { x.classList.toggle('liste', w === 'liste'); });
      document.querySelectorAll('.umschalter').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.ansicht === w)); });
    }
    try { ansicht(localStorage.getItem(ANSICHT) === 'liste' ? 'liste' : 'kacheln'); } catch (e) { ansicht('kacheln'); }
    document.querySelectorAll('.umschalter').forEach(function (b) { b.addEventListener('click', function () {
      ansicht(b.dataset.ansicht); try { localStorage.setItem(ANSICHT, b.dataset.ansicht); } catch (e) { /* nur jetzt */ }
    }); });
    if (vfeld) vfeld.value = liesVersion();
    [suche, art, kat, autor, vfeld, nur, lokal].forEach(function (x) { if (x) x.addEventListener(x.tagName === 'INPUT' && x.type !== 'checkbox' ? 'input' : 'change', function () {
      if (x === vfeld) { var w = vfeld.value.trim(); if (!w || VERSION.test(w)) merkeVersion(w); }
      filtern();
    }); });
    filtern();
  }
  // Paketseite: Hinweis „passt / ältere Version / braucht neueres DMS“ unter dem Kopf.
  var kopf = document.querySelector('.paketkopf[data-versionen]'), feld = document.getElementById('dms-passt');
  function zeigePaket() {
    var versionen = JSON.parse(kopf.dataset.versionen), dms = liesVersion(), r = pruefe(versionen, dms), id = kopf.dataset.paket;
    var knopf = kopf.querySelector('.installieren');
    feld.className = 'dms-passt'; feld.textContent = ''; if (knopf) knopf.hidden = false;
    if (!r) {
      feld.innerHTML = '<p class="leise">Passt das Paket zu deinem Ablago? Deine Ablago-Version: <input id="dms-version-paket" inputmode="decimal" placeholder="z. B. 0.144.2" aria-label="Deine Ablago-Version"> <span class="klein">(steht in Ablago unter „Über Ablago“, bleibt nur in diesem Browser)</span></p>';
      var i = document.getElementById('dms-version-paket');
      i.addEventListener('change', function () { var w = i.value.trim(); if (VERSION.test(w)) { merkeVersion(w); zeigePaket(); } });
      return;
    }
    var aendern = ' <a href="#" data-dms-version-aendern>ändern</a>';
    if (r.fall === 'ja') { feld.className += ' ja'; feld.innerHTML = 'Passt zu deinem Ablago ' + dms + '.' + aendern; return; }
    if (knopf) knopf.hidden = true;
    feld.className += ' warn';
    var html = '<p><strong>Für Version ' + r.neu[0] + ' brauchst du Ablago ' + mindestens(r.neu[1]) + ' oder neuer</strong> – du hast ' + dms + '.' + aendern + '</p>'
      + '<p>Aktualisiere dein Ablago, damit du dieses Paket mit allen Verbesserungen und Fehlerbehebungen nutzen kannst.</p>'
      + '<p><a class="knopf primaer" href="https://help.ablago.app/admin/aktuell/aktualisieren/">So aktualisierst du dein Ablago →</a></p>';
    if (r.fall === 'aelter') html += '<p class="aelter-link"><a href="#" data-installieren="' + id + '@' + r.version + '">Ältere Version ' + r.version + ' trotzdem installieren</a> <span class="leise">– ihr fehlen Verbesserungen und Fehlerbehebungen. Nach Ablago-Update holst du die neue Version über die Paketverwaltung nach.</span></p>';
    feld.innerHTML = html;
  }
  if (kopf && feld) {
    feld.addEventListener('click', function (e) { if (e.target.closest('[data-dms-version-aendern]')) { e.preventDefault(); merkeVersion(''); zeigePaket(); } });
    zeigePaket();
  }
})();
