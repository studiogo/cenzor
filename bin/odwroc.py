#!/usr/bin/env python3
"""Wstawia prawdziwe nazwy z powrotem do tekstu, ktory wrocil z etykietami."""
import argparse, json, sys
from pathlib import Path


def main():
    # Windows zapisuje wyjscie przekierowane do pliku w cp1250 — polska litera
    # w sciezce wywraca wtedy program. Na Macu i Linuksie to nic nie zmienia.
    for strumien in (sys.stdout, sys.stderr):
        if hasattr(strumien, "reconfigure"):
            strumien.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Odwraca anonimizacje wedlug slownika.")
    p.add_argument("plik", help="tekst z etykietami")
    p.add_argument("slownik", help="plik -slownik.json z anonimizacji")
    p.add_argument("-o", "--wyjscie", help="plik wynikowy (domyslnie <nazwa>-odtworzony.txt)")
    args = p.parse_args()

    zrodlo, slownik_plik = Path(args.plik), Path(args.slownik)
    for f in (zrodlo, slownik_plik):
        if not f.exists():
            sys.exit(f"Nie ma pliku: {f}")

    tekst = zrodlo.read_text(encoding="utf-8")
    slownik = json.loads(slownik_plik.read_text(encoding="utf-8"))

    wstawione = 0
    # dluzsze etykiety najpierw, zeby [OSOBA_10] nie ucierpialo przez [OSOBA_1]
    for etykieta in sorted(slownik, key=len, reverse=True):
        ile = tekst.count(etykieta)
        if ile:
            tekst = tekst.replace(etykieta, slownik[etykieta])
            wstawione += ile

    nieuzyte = [e for e in slownik if e not in tekst and slownik[e] not in tekst]
    wyjscie = Path(args.wyjscie) if args.wyjscie else zrodlo.with_name(zrodlo.stem + "-odtworzony" + zrodlo.suffix)
    wyjscie.write_text(tekst, encoding="utf-8")

    print(f"Wstawiono z powrotem: {wstawione} wystapien.")
    if nieuzyte:
        print(f"Etykiet nieobecnych w tekscie: {len(nieuzyte)} (to normalne, jesli tekst jest skrotem).")
    print(f"Wynik: {wyjscie}")


if __name__ == "__main__":
    main()
