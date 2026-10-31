// Katalog-Webseite der DMS-Registry: Suche/Filter und „In meinem DMS installieren“.
// Die Adresse des eigenen DMS bleibt nur in diesem Browser (localStorage).
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
  var suche = document.getElementById('suche'), art = document.getElementById('art');
  function filtern() {
    var q = (suche.value || '').trim().toLowerCase(), a = art.value, n = 0;
    document.querySelectorAll('.kachel').forEach(function (k) {
      var ok = (!q || k.dataset.suche.indexOf(q) >= 0) && (!a || k.dataset.art === a);
      k.hidden = !ok; if (ok) n++;
    });
    document.getElementById('keine').hidden = n > 0;
  }
  if (suche) { suche.addEventListener('input', filtern); art.addEventListener('change', filtern); }
})();
