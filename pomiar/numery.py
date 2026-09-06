#!/usr/bin/env python3
"""Sprawdzian wykrywania polskich numerow.

Buduje numery o znanej poprawnosci (z policzonymi cyframi kontrolnymi), wkłada
kazdy w zdanie takie, jakie spotyka sie w pismach, i sprawdza, czy narzedzie je
wycielo. Osobno liczy falszywe alarmy: te same wzorce puszczone na dokumentach
poligonu, w ktorych zadnego z tych numerow nie ma.

    python3 numery.py [katalog-poligonu]
"""
import random, re, subprocess, sys, tempfile
from pathlib import Path

KAT = Path(__file__).resolve().parent
SKILL = KAT.parent
sys.path.insert(0, str(SKILL / "bin"))
import anonimizuj as A


def cyfry(n, r):
    return "".join(str(r.randrange(10)) for _ in range(n))


def gen_pesel(r):
    """PESEL musi zawierac istniejaca date urodzenia — samo dopasowanie sumy
    kontrolnej nie wystarczy, narzedzie sprawdza tez date."""
    while True:
        rok = r.randrange(40, 99)
        mies = r.randrange(1, 13)
        dzien = r.randrange(1, 29)
        c = f"{rok:02d}{mies:02d}{dzien:02d}" + cyfry(4, r)
        w = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        k = (10 - sum(int(c[i]) * w[i] for i in range(10)) % 10) % 10
        if A._suma_pesel(c + str(k)):
            return c + str(k)


def gen_nip(r):
    while True:
        c = cyfry(9, r)
        w = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        k = sum(int(c[i]) * w[i] for i in range(9)) % 11
        if k != 10 and A._suma_nip(c + str(k)):
            return c + str(k)


def gen_regon(r):
    while True:
        c = cyfry(8, r)
        w = [8, 9, 2, 3, 4, 5, 6, 7]
        s = sum(int(c[i]) * w[i] for i in range(8)) % 11
        k = 0 if s == 10 else s
        if A._suma_regon(c + str(k)):
            return c + str(k)


def gen_paszport(r):
    litery = "".join(r.choice("ABCDEFGHIJKLMNOPRSTUWYZ") for _ in range(2))
    for _ in range(400):
        n = litery + cyfry(7, r)
        if A._suma_paszport(n):
            return n
    return None


def gen_pwz(r):
    for _ in range(400):
        c = cyfry(6, r)
        k = sum(int(c[i]) * (i + 1) for i in range(6)) % 11
        if k < 10 and k != 0:
            return str(k) + c
    return None


def gen_imei(r):
    c = cyfry(14, r)
    for k in range(10):
        if A._luhn(c + str(k)):
            return c + str(k)
    return None


def gen_kw(r):
    kod = "WA4M"
    for _ in range(400):
        n = cyfry(8, r)
        for k in range(10):
            if A._suma_kw(f"{kod}/{n}/{k}"):
                return f"{kod}/{n}/{k}"
    return None


def zdania(r):
    """(nazwa, zdanie, numer, oczekiwana etykieta)"""
    p = []
    x = gen_pesel(r);      p.append(("PESEL", f"Pan Kowalski, PESEL {x}, zlozyl wniosek.", x, "PESEL"))
    x = gen_nip(r);        p.append(("NIP", f"Firma o numerze NIP {x} wystawila fakture.", x, "NIP"))
    x = gen_regon(r);      p.append(("REGON", f"Podmiot REGON {x} zostal wpisany do rejestru.", x, "REGON"))
    x = gen_paszport(r);   p.append(("paszport", f"Legitymuje sie paszportem {x} wydanym w 2019 r.", x, "PASZPORT"))
    x = gen_pwz(r);        p.append(("PWZ lekarza", f"Lekarz, prawo wykonywania zawodu {x}, wystawil zaswiadczenie.", x, "PWZ_LEKARZA"))
    x = gen_imei(r);       p.append(("IMEI", f"Zgloszono kradziez telefonu IMEI {x}.", x, "IMEI"))
    x = gen_kw(r);         p.append(("ksiega wieczysta", f"Nieruchomosc ma urzadzona ksiege wieczysta {x}.", x, "KSIEGA_WIECZYSTA"))
    p.append(("KRS ze slowem", "Spolka wpisana do rejestru KRS 0000713345.", "0000713345", "KRS"))
    p.append(("KRS bez slowa", "Spolke wpisano pod nr 0000345678 dnia 12 stycznia.", "0000345678", "KRS"))
    p.append(("dowod osobisty", "Dowod osobisty ABC123456 wydany przez prezydenta miasta.", "ABC123456", "DOWOD"))
    p.append(("kod pocztowy", "Adres: ul. Kwiatowa 5, 00-950 Warszawa.", "00-950", "KOD"))
    p.append(("konto bankowe", "Wplata na konto 61 1090 1014 0000 0712 1981 2874.", "61 1090 1014 0000 0712 1981 2874", "KONTO"))
    p.append(("telefon z kotwica", "Kontakt: tel. 601 234 567 w godzinach pracy.", "601 234 567", "TELEFON"))
    p.append(("telefon +48", "Prosze dzwonic +48 601 234 567 po poludniu.", "+48 601 234 567", "TELEFON"))
    p.append(("e-mail", "Pisz na adres jan.kowalski@example.pl w tej sprawie.", "jan.kowalski@example.pl", "MAIL"))
    p.append(("VIN", "Pojazd o numerze VIN 1HGBH41JXMN109186 zostal zatrzymany.", "1HGBH41JXMN109186", "VIN"))
    p.append(("prawo jazdy", "Prawo jazdy 12345678901 zostalo zatrzymane przez policje.", "12345678901", "PRAWO_JAZDY"))
    p.append(("producent rolny", "Wnioskodawca, numer producenta 123456789, ubiega sie o doplate.", "123456789", "NR_PRODUCENTA"))
    p.append(("BDO", "Podmiot posiada numer BDO 000012345 w rejestrze.", "000012345", None))
    p.append(("karta pobytu", "Cudzoziemiec, karta pobytu AB1234567, przebywa legalnie.", "AB1234567", "KARTA_POBYTU"))
    p.append(("recepta", "Recepta o numerze 0103000012345678901234 zostala zrealizowana.", "0103000012345678901234", "RECEPTA"))
    p.append(("dzialka", "Dzialka ewidencyjna 146501_1.0001.123/4 o powierzchni 0,25 ha.", "146501_1.0001.123/4", "DZIALKA"))
    p.append(("numer rejestracyjny", "Pojazd o numerze rejestracyjnym WA12345 zostal odholowany.", "WA12345", "NR_REJ"))
    return p


def main():
    r = random.Random(20260904)
    konfig = A.wczytaj_konfig()
    konfig["jezyk"] = "pl"
    proby = zdania(r)

    print("SPRAWDZIAN WYKRYWANIA — kazdy numer w zdaniu z prawdziwego pisma\n")
    trafione = 0
    for nazwa, zdanie, numer, etykieta in proby:
        trafienia = A.znajdz(zdanie, konfig)
        czysty, _ = A.podmien(zdanie, trafienia)
        wyciety = numer not in czysty
        etykiety = {A.ETYKIETY.get(t, t) for _, _, t, _ in trafienia}
        trafione += wyciety
        znak = "TAK" if wyciety else "NIE"
        jako = ", ".join(sorted(etykiety)) if etykiety else "-"
        print(f"  {nazwa:22} {znak:4} jako: {jako}")
    print(f"\n  Wyciete: {trafione} z {len(proby)}")

    kat = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not kat or not kat.exists():
        print("\n(pomijam falszywe alarmy — nie podano katalogu poligonu)")
        return
    print("\nFALSZYWE ALARMY — te same wzorce na dokumentach, w ktorych tych numerow nie ma\n")
    interesujace = {"PASZPORT", "PWZ_LEKARZA", "IMEI", "KSIEGA_WIECZYSTA", "VIN",
                    "PRAWO_JAZDY", "NR_PRODUCENTA", "BDO", "KARTA_POBYTU",
                    "RECEPTA", "DZIALKA", "KRS"}
    licznik = {e: [] for e in interesujace}
    pliki = [f for f in sorted(kat.glob("*.txt")) if "-anon" not in f.name]
    for f in pliki:
        tekst = f.read_text(encoding="utf-8", errors="replace")
        for _, _, typ, fragment in A.znajdz(tekst, konfig):
            e = A.ETYKIETY.get(typ, typ)
            if e in interesujace:
                licznik[e].append(fragment)
    slow = sum(len(f.read_text(encoding="utf-8", errors="replace").split()) for f in pliki)
    print(f"  dokumentow: {len(pliki)}, slow: {slow}")
    for e in sorted(interesujace):
        ile = len(licznik[e])
        prz = f" — np. {licznik[e][:3]}" if ile else ""
        print(f"  {e:20} {ile}{prz}")


if __name__ == "__main__":
    main()
