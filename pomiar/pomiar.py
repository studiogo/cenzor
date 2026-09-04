#!/usr/bin/env python3
"""Mierzy szczelnosc anonimizacji na katalogu dokumentow.

Dla kazdego pliku .txt: uruchamia anonimizacje, potem sprawdza, ile danych
z listy prawdy zostalo w pliku "do wyslania". Zapisuje wynik jako JSON i tabele.

    python3 pomiar.py <katalog-z-dokumentami> [--jezyk pl]

Dokumenty NIE sa czescia repozytorium — sciezki do nich sa w pomiar/ZRODLA.md.
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import date
from pathlib import Path

KAT = Path(__file__).resolve().parent
SKILL = KAT.parent
PYTHON = str(SKILL / "venv" / "bin" / "python")
SKRYPT = str(SKILL / "bin" / "anonimizuj.py")

IMIONA = {w for w in (KAT / "imiona.txt").read_text(encoding="utf-8").split() if w}

# Odmiana: "Janem", "Annie" — porownujemy po pierwszych literach imienia.
RDZENIE = {i[:-1] if len(i) > 4 else i for i in IMIONA}


def osoby(tekst):
    """Imie z listy + nastepny wyraz z wielkiej litery = nazwisko osoby."""
    znalezione = set()
    for m in re.finditer(r"\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\-]{2,})\b", tekst):
        imie, nazwisko = m.group(1), m.group(2)
        if imie in IMIONA or any(imie.startswith(r) for r in RDZENIE):
            znalezione.add(m.group(0))
    return znalezione


KONTROLE = {
    "PESEL":     lambda t: set(re.findall(r"\bPESEL[:\s]*([0-9]{11})", t, re.I)),
    "NIP":       lambda t: set(re.findall(r"\bNIP[:\s]*([0-9][0-9 .\-]{8,15}[0-9])", t, re.I)),
    "REGON":     lambda t: set(re.findall(r"\bREGON[:\s]*([0-9]{9,14})", t, re.I)),
    "KRS":       lambda t: set(re.findall(r"\bKRS[:\s]*([0-9]{5,10})", t, re.I)),
    "konto":     lambda t: set(re.findall(r"\b(?:PL)?[0-9]{2}(?:[ -]?[0-9]{4}){6}\b", t)),
    "mail":      lambda t: set(re.findall(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", t)),
    "telefon":   lambda t: set(re.findall(r"\b(?:tel|telefon\w{0,2}|fax|faks|kom)\b\.?[^0-9\n]{0,20}((?:[0-9][\s()-]{0,3}){6,12}[0-9])", t, re.I)),
    "kod_pocztowy": lambda t: set(re.findall(r"(?<![0-9-])[0-9]{2}-[0-9]{3}(?![0-9-])(?=[^\n]{0,30}[A-ZĄĆĘŁŃÓŚŹŻ])", t)),
    "osoba":     osoby,
    "organizacja": lambda t: set(re.findall(r"(?:Fundacja|Stowarzyszenie|Towarzystwo|Klub|Związek)\s+[„\"']?[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż]{2,}(?:\s+[\wąćęłńóśźż]{2,}){0,3}", t)),
    "firma":     lambda t: set(re.findall(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][\w\-\.]{2,}(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w\-\.]+)*\s+(?:sp\.\s*z\s*o\.o\.|S\.A\.)", t, re.I)),
}


def main():
    p = argparse.ArgumentParser(description="Mierzy szczelnosc anonimizacji.")
    p.add_argument("katalog", help="katalog z dokumentami .txt")
    p.add_argument("--jezyk", default="pl", choices=["pl", "en"])
    p.add_argument("--prog", type=float, default=89.0, help="prog zaliczenia w procentach")
    args = p.parse_args()

    pliki = sorted(f for f in Path(args.katalog).glob("*.txt")
                   if "-anon" not in f.name and "odtworzony" not in f.name)
    if not pliki:
        sys.exit(f"Brak dokumentow .txt w {args.katalog}")

    wynik, sumy, odwracalne = {}, {k: [0, 0] for k in KONTROLE}, [0, 0]
    for f in pliki:
        t0 = time.time()
        r = subprocess.run([PYTHON, SKRYPT, str(f), "--jezyk", args.jezyk],
                           capture_output=True, text=True)
        anon = f.with_name(f.stem + "-anon" + f.suffix)
        if not anon.exists():
            print(f"BLAD {f.name}: {r.stderr[-160:]}")
            continue
        orig_t = f.read_text(encoding="utf-8", errors="replace")
        anon_t = anon.read_text(encoding="utf-8", errors="replace")

        # odwracalnosc
        slownik = anon.with_name(anon.stem + "-slownik.json")
        subprocess.run([PYTHON, str(SKILL / "bin" / "odwroc.py"), str(anon), str(slownik)],
                       capture_output=True, text=True)
        odtw = anon.with_name(anon.stem + "-odtworzony" + anon.suffix)
        odwracalne[1] += 1
        if odtw.exists() and odtw.read_text(encoding="utf-8", errors="replace") == orig_t:
            odwracalne[0] += 1
        for x in (anon, slownik, odtw):
            x.unlink(missing_ok=True)

        wpis = {}
        for nazwa, szukaj in KONTROLE.items():
            bylo = szukaj(orig_t)
            zostalo = sorted(x for x in bylo if x in anon_t)
            wpis[nazwa] = {"bylo": len(bylo), "zostalo": len(zostalo), "przyklady": zostalo[:5]}
            sumy[nazwa][0] += len(bylo)
            sumy[nazwa][1] += len(zostalo)
        wynik[f.name] = wpis
        print(f"{f.name:36} {time.time()-t0:5.1f}s")

    raport = {
        "data": str(date.today()),
        "jezyk": args.jezyk,
        "poligon": Path(args.katalog).name,
        "dokumentow": len(wynik),
        "slow": sum(len(Path(args.katalog, n).read_text(encoding='utf-8', errors='replace').split()) for n in wynik),
        "odwracalnosc": f"{odwracalne[0]}/{odwracalne[1]}",
        "kategorie": {}, "per_dokument": wynik,
    }
    for k, (bylo, zostalo) in sumy.items():
        if bylo:
            raport["kategorie"][k] = {"bylo": bylo, "przeszlo": zostalo,
                                      "wyciete_proc": round(100 * (bylo - zostalo) / bylo, 1)}

    KAT.mkdir(exist_ok=True)
    plik = KAT / f"wynik-{Path(args.katalog).name}-{raport['data']}.json"
    plik.write_text(json.dumps(raport, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nDokumentow: {raport['dokumentow']}  slow: {raport['slow']}  "
          f"odwracalnosc: {raport['odwracalnosc']}\n")
    print(f"{'kategoria':16} {'bylo':>6} {'przeszlo':>9} {'wyciete':>9}   ocena")
    ponizej = []
    for k, v in raport["kategorie"].items():
        ocena = "ok" if v["wyciete_proc"] >= args.prog else "PONIZEJ PROGU"
        if v["wyciete_proc"] < args.prog:
            ponizej.append(k)
        print(f"{k:16} {v['bylo']:>6} {v['przeszlo']:>9} {v['wyciete_proc']:>8}%   {ocena}")
    print(f"\nZapisano: {plik}")
    if ponizej:
        print("Ponizej progu:", ", ".join(ponizej))
    return 1 if ponizej else 0


if __name__ == "__main__":
    sys.exit(main())
