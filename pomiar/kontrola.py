#!/usr/bin/env python3
"""Niezalezny pomiar kontrolny nazwisk.

pomiar.py szuka osob po liscie imion — tej samej, ktorej uzywa anonimizacja.
To by znaczylo mierzenie wlasnym przyrzadem. Tutaj liste prawdy buduje SAM
model jezykowy spaCy na oryginale, bez zadnej listy. Potem sprawdzamy,
ile z tych nazwisk zostalo w pliku "do wyslania".

Liczymy tez nadmiar: ile fragmentow wycieto, choc model nie uznal ich za osobe.

    python3 kontrola.py <katalog-z-dokumentami>
"""
import json, re, subprocess, sys
from datetime import date
from pathlib import Path

KAT = Path(__file__).resolve().parent
SKILL = KAT.parent
PYTHON = str(SKILL / "venv" / "bin" / "python")

KOD = r'''
import json, subprocess, sys
from pathlib import Path
import spacy
nlp = spacy.load("pl_core_news_lg")
nlp.max_length = 3_000_000
wynik = {}
for sciezka in sys.argv[1:]:
    p = Path(sciezka)
    orig = p.read_text(encoding="utf-8", errors="replace")
    anon_p = p.with_name(p.stem + "-anon" + p.suffix)
    anon = anon_p.read_text(encoding="utf-8", errors="replace") if anon_p.exists() else ""
    ents = {e.text.strip() for e in nlp(orig).ents
            if e.label_ == "persName" and len(e.text.strip()) > 3}
    osoby = sorted(ents)
    # Wskaznik ostry: tylko imie + nazwisko, dwa wyrazy z wielkiej litery.
    # Odsiewa nazwy ulic ("Krasinskiego") i urwane wyrazy z PDF-a, ktore
    # model tez oznacza jako osobe.
    pelne = sorted(e for e in ents
                   if len(e.split()) >= 2
                   and all(w[:1].isupper() and w[:1].isalpha() for w in e.split()))
    zostaly = [o for o in osoby if o in anon]
    zostaly_pelne = [o for o in pelne if o in anon]
    wynik[p.name] = {"bylo": len(osoby), "zostalo": len(zostaly), "przyklady": zostaly[:6],
                     "pelne_bylo": len(pelne), "pelne_zostalo": len(zostaly_pelne),
                     "pelne_przyklady": zostaly_pelne[:6]}
print(json.dumps(wynik, ensure_ascii=False))
'''


def main():
    kat = Path(sys.argv[1] if len(sys.argv) > 1 else "poligon")
    pliki = sorted(f for f in kat.glob("*.txt")
                   if "-anon" not in f.name and "odtworzony" not in f.name)
    for f in pliki:
        anon = f.with_name(f.stem + "-anon" + f.suffix)
        if not anon.exists():
            subprocess.run([PYTHON, str(SKILL / "bin" / "anonimizuj.py"), str(f), "--jezyk", "pl"],
                           capture_output=True, text=True)
    r = subprocess.run([PYTHON, "-c", KOD] + [str(f) for f in pliki],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-500:])
    dane = json.loads(r.stdout)
    bylo = sum(v["bylo"] for v in dane.values())
    zostalo = sum(v["zostalo"] for v in dane.values())
    proc = round(100 * (bylo - zostalo) / bylo, 1) if bylo else 0.0
    pb = sum(v["pelne_bylo"] for v in dane.values())
    pz = sum(v["pelne_zostalo"] for v in dane.values())
    pproc = round(100 * (pb - pz) / pb, 1) if pb else 0.0
    raport = {"data": str(date.today()), "metoda": "lista prawdy z modelu spaCy, bez listy imion",
              "osoby_bylo": bylo, "osoby_przeszlo": zostalo, "wyciete_proc": proc,
              "pelne_nazwiska_bylo": pb, "pelne_nazwiska_przeszlo": pz,
              "pelne_nazwiska_wyciete_proc": pproc,
              "per_dokument": dane}
    (KAT / f"kontrola-{kat.name}-{raport['data']}.json").write_text(
        json.dumps(raport, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wszystko, co model uznal za osobe: {bylo}  przeszlo: {zostalo}  wyciete: {proc}%")
    print(f"   (ta liczba zawiera szum: nazwy ulic, urwane wyrazy z PDF-a)")
    print(f"Pelne nazwiska (imie + nazwisko): {pb}  przeszlo: {pz}  wyciete: {pproc}%")
    for f, v in dane.items():
        if v["pelne_zostalo"]:
            print(f"  {f[:30]:30} {v['pelne_zostalo']}/{v['pelne_bylo']}  {v['pelne_przyklady']}")


if __name__ == "__main__":
    main()
