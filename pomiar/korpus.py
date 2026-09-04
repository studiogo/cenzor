#!/usr/bin/env python3
"""Pomiar na korpusie z adnotacja zrobiona przez ludzi.

Nasz podstawowy pomiar buduje liste prawdy modelem spaCy — a tego samego modelu
uzywa anonimizacja. Tutaj listy prawdy nie buduje zadna maszyna: nazwiska
oznaczyli ludzie, ktorzy tworzyli Korpus Jezyka Polskiego Politechniki
Wroclawskiej (KPWr, licencja CC BY 3.0).

    python3 korpus.py kpwr-test.iob
"""
import subprocess, sys, tempfile
from pathlib import Path

KAT = Path(__file__).resolve().parent
SKILL = KAT.parent
sys.path.insert(0, str(SKILL / "bin"))
import anonimizuj as A


def wczytaj(sciezka):
    """Zwraca (tekst dokumentu, lista nazwisk oznaczonych przez czlowieka)."""
    zdania, osoby = [], []
    biezace, osoba = [], []
    for linia in Path(sciezka).read_text(encoding="utf-8").splitlines():
        if linia.startswith("-DOCSTART"):
            continue
        if not linia.strip():
            if biezace:
                zdania.append(" ".join(biezace)); biezace = []
            if osoba:
                osoby.append(" ".join(osoba)); osoba = []
            continue
        czesci = linia.split("\t")
        if len(czesci) < 4:
            continue
        slowo, znacznik = czesci[0], czesci[3]
        biezace.append(slowo)
        if znacznik.startswith("B-nam_liv_person"):
            if osoba:
                osoby.append(" ".join(osoba))
            osoba = [slowo]
        elif znacznik.startswith("I-nam_liv_person"):
            osoba.append(slowo)
        elif osoba:
            osoby.append(" ".join(osoba)); osoba = []
    if biezace:
        zdania.append(" ".join(biezace))
    if osoba:
        osoby.append(" ".join(osoba))
    return "\n".join(zdania), osoby


def main():
    plik = sys.argv[1] if len(sys.argv) > 1 else "kpwr-test.iob"
    tekst, osoby = wczytaj(plik)
    print(f"Korpus: {len(tekst.split())} slow, {len(osoby)} oznaczen osob "
          f"({len(set(osoby))} roznych)\n")

    konfig = A.wczytaj_konfig()
    konfig["jezyk"] = "pl"
    trafienia = A.znajdz(tekst, konfig)
    czysty, _ = A.podmien(tekst, trafienia)

    # Liczymy po roznych nazwiskach: czy dana osoba zostala w tekscie "do wyslania".
    rozne = sorted(set(osoby))
    pelne = [o for o in rozne if len(o.split()) >= 2]
    zostaly = [o for o in rozne if o in czysty]
    zostaly_pelne = [o for o in pelne if o in czysty]

    def procent(ile, z):
        return f"{100 * (z - ile) / z:.1f}%" if z else "-"

    print(f"Wszystkie oznaczenia osob: {len(rozne)}  zostalo: {len(zostaly)}  "
          f"wyciete: {procent(len(zostaly), len(rozne))}")
    print(f"Pelne nazwiska (dwa czlony): {len(pelne)}  zostalo: {len(zostaly_pelne)}  "
          f"wyciete: {procent(len(zostaly_pelne), len(pelne))}")
    print("\nPrzyklady tego, co przeszlo:", zostaly[:15])


if __name__ == "__main__":
    main()
