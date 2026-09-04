#!/usr/bin/env python3
"""Pobiera dokumenty poligonu z BIP-ow na Twoj dysk.

Dokumentow NIE ma w repozytorium — sa w nich nazwiska prawdziwych ludzi.
Sa jawne z mocy prawa w Biuletynach Informacji Publicznej, ale ich kopiowanie
do repozytorium byloby osobnym przetwarzaniem cudzych danych.

    python3 pobierz.py [katalog-docelowy]

Wymaga pdftotext (pakiet poppler).
"""
import re, subprocess, sys, urllib.request
from pathlib import Path

KAT = Path(__file__).resolve().parent
NAGLOWEK = {"User-Agent": "Mozilla/5.0 (anonimizuj-pl/pomiar)"}


def zrodla():
    for linia in (KAT / "ZRODLA.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d\d-[\w-]+)\s+(https?://\S+)", linia.strip())
        if m:
            yield m.group(1), m.group(2)


def main():
    cel = Path(sys.argv[1] if len(sys.argv) > 1 else "poligon")
    cel.mkdir(parents=True, exist_ok=True)
    for nazwa, url in zrodla():
        pdf, txt = cel / f"{nazwa}.pdf", cel / f"{nazwa}.txt"
        if txt.exists():
            print(f"jest juz: {nazwa}")
            continue
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=NAGLOWEK), timeout=40) as o:
                pdf.write_bytes(o.read())
            subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
            print(f"pobrano: {nazwa}  ({len(txt.read_text(encoding='utf-8', errors='replace').split())} slow)")
        except Exception as e:
            print(f"NIE UDALO SIE: {nazwa} — {e}")
    print(f"\nGotowe. Pomiar: python3 {KAT / 'pomiar.py'} {cel}")


if __name__ == "__main__":
    main()
