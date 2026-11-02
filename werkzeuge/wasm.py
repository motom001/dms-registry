"""Prüft ein gebautes Modul gegen die DMS-Paket-ABI 1 (wie das DMS beim Installieren).

Erlaubt sind nur Importe aus wasi_snapshot_preview1 (Funktionen), dms (die Funktionen unten) und der
Speicher env.memory; das Modul muss dms_puffer und dms_ereignis exportieren.
"""
DMS_FUNKTIONEN = {'api', 'api_binaer', 'netz', 'datei', 'antwort_laenge', 'antwort_lesen', 'ergebnis', 'log',
                  'speicher_lesen', 'speicher_schreiben',
                  # ab DMS 0.124.0 (DMS #444): Antwort Stück für Stück lesen und weitergeben
                  'netz_strom', 'netz_weiter', 'teil'}
ARTEN = {0: 'function', 1: 'table', 2: 'memory', 3: 'global', 4: 'tag'}


class _Leser:
    def __init__(self, b: bytes, p: int = 0):
        self.b, self.p = b, p

    def leb(self) -> int:
        r = s = 0
        while True:
            x = self.b[self.p]; self.p += 1
            r |= (x & 0x7f) << s; s += 7
            if not x & 0x80:
                return r

    def name(self) -> str:
        n = self.leb(); t = self.b[self.p:self.p + n].decode('utf-8'); self.p += n
        return t

    def grenzen(self):
        flags = self.leb(); mn = self.leb(); mx = self.leb() if flags & 1 else None
        return flags, mn, mx


def lies(b: bytes):
    """Importe [(modul, name, art)] und Exporte {name: art}."""
    if b[:4] != b'\0asm' or b[4:8] != b'\x01\0\0\0':
        raise ValueError('kein WebAssembly-Modul (Version 1)')
    l = _Leser(b, 8)
    importe, exporte = [], {}
    while l.p < len(b):
        sid = b[l.p]; l.p += 1
        groesse = l.leb(); ende = l.p + groesse
        if sid == 2:
            for _ in range(l.leb()):
                modul, name, art = l.name(), l.name(), b[l.p]; l.p += 1
                if art == 0: l.leb()
                elif art == 1: l.p += 1; l.grenzen()
                elif art == 2: l.grenzen()
                elif art == 3: l.p += 2
                elif art == 4: l.p += 1; l.leb()
                importe.append((modul, name, ARTEN.get(art, str(art))))
        elif sid == 7:
            for _ in range(l.leb()):
                name, art = l.name(), b[l.p]; l.p += 1; l.leb()
                exporte[name] = ARTEN.get(art, str(art))
        l.p = ende
    return importe, exporte


def dms_importe(b: bytes) -> set[str]:
    """Namen der importierten Funktionen aus dms (leer, wenn das Modul sich nicht lesen lässt)."""
    try:
        importe, _ = lies(b)
    except (ValueError, IndexError, UnicodeDecodeError):
        return set()
    return {n for m, n, a in importe if m == 'dms' and a == 'function'}


def pruefe(b: bytes) -> list[str]:
    try:
        importe, exporte = lies(b)
    except (ValueError, IndexError, UnicodeDecodeError) as e:
        return [f'code/modul.wasm: {e}']
    fehler = []
    fremd = [f'{m}.{n}' for m, n, a in importe
             if not (m == 'wasi_snapshot_preview1' and a == 'function')
             and not (m == 'dms' and a == 'function' and n in DMS_FUNKTIONEN)
             and not (m == 'env' and n == 'memory' and a == 'memory')]
    if fremd:
        fehler.append(f'code/modul.wasm: unbekannte Importe {", ".join(fremd[:5])}')
    if not any(a == 'memory' for _, _, a in importe):
        fehler.append('code/modul.wasm: importiert keinen Speicher – mit -Wl,--import-memory bauen')
    for f in ('dms_puffer', 'dms_ereignis'):
        if exporte.get(f) != 'function':
            fehler.append(f'code/modul.wasm: Export {f} fehlt')
    return fehler
