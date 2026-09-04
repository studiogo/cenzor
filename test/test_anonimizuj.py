"""Straznik narzedzia — sprawdza, czy po zmianie w kodzie nadal dziala to,
co dzialalo wczoraj.

Kazdy test to jedno zdanie zapisane tak, ze komputer umie je sam sprawdzic:
"dam narzedziu to, oczekuje tego". Uruchomienie:

    venv/bin/python -m pytest test/ -q
"""
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "bin"))
import anonimizuj as A


@pytest.fixture(scope="module")
def konfig():
    k = A.wczytaj_konfig()
    k["jezyk"] = "pl"
    return k


def wytnij(tekst, konfig):
    return A.podmien(tekst, A.znajdz(tekst, konfig))[0]


# --- Sumy kontrolne: numer sam potwierdza swoja poprawnosc ---

def test_pesel_przyjmuje_poprawny_odrzuca_podrobiony():
    assert A._suma_pesel("85010112345")
    assert not A._suma_pesel("85010112346")


def test_pesel_tylko_jedna_cyfra_konczaca_jest_dobra():
    """Suma kontrolna ma sens tylko wtedy, gdy z dziesieciu mozliwych
    zakonczen numeru przechodzi dokladnie jedno."""
    warianty = ["8501011234" + str(c) for c in range(10)]
    assert sum(A._suma_pesel(w) for w in warianty) == 1


def test_nip_odsiewa_zla_cyfre():
    assert A._suma_nip("5260250274")          # NIP z przykladowego pisma
    assert not A._suma_nip("5260250275")


def test_paszport_z_dokumentacji():
    # Numer podany w opisie budowy polskiego paszportu.
    assert A._suma_paszport("CC7999486")
    assert not A._suma_paszport("CC7999487")


def test_ksiega_wieczysta_politechniki():
    # Numer ksiegi wieczystej Politechniki Warszawskiej z dokumentacji.
    assert A._suma_kw("WA4M/00160286/2")
    assert not A._suma_kw("WA4M/00160286/5")


def test_numer_lekarza_z_izby_lekarskiej():
    # Przyklad z zasad weryfikacji Naczelnej Izby Lekarskiej.
    assert A._suma_pwz("5425740")
    assert not A._suma_pwz("5425741")
    assert not A._suma_pwz("0425740")     # nie zaczyna sie od zera


def test_imei_luhn():
    assert A._luhn("490154203237518")
    assert not A._luhn("490154203237519")


# --- Wycinanie w prawdziwym zdaniu ---

@pytest.mark.parametrize("zdanie, numer", [
    ("Powod: Jan Kowalski, PESEL 85010112345, zam. w Opolu.", "85010112345"),
    ("Firma o numerze NIP 5260250274 wystawila fakture.", "5260250274"),
    ("Legitymuje sie paszportem CC7999486 wydanym w 2019 r.", "CC7999486"),
    ("Lekarz, prawo wykonywania zawodu 5425740, wystawil zaswiadczenie.", "5425740"),
    ("Zgloszono kradziez telefonu IMEI 490154203237518.", "490154203237518"),
    ("Nieruchomosc ma ksiege wieczysta WA4M/00160286/2.", "WA4M/00160286/2"),
    ("Spolke wpisano pod nr 0000713345 dnia 12 stycznia.", "0000713345"),
    ("Dowod osobisty ABC123456 wydany przez prezydenta miasta.", "ABC123456"),
    ("Adres: ul. Kwiatowa 5, 00-950 Warszawa.", "00-950"),
    ("Kontakt: tel. 601 234 567 w godzinach pracy.", "601 234 567"),
    ("Prosze dzwonic +48 601 234 567 po poludniu.", "+48 601 234 567"),
    ("Pisz na adres jan.kowalski@example.pl w tej sprawie.", "jan.kowalski@example.pl"),
    ("Pojazd o numerze VIN 1HGBH41JXMN109186 zostal zatrzymany.", "1HGBH41JXMN109186"),
    ("Prawo jazdy 12345678901 zostalo zatrzymane.", "12345678901"),
    ("Wnioskodawca, numer producenta 123456789, ubiega sie o doplate.", "123456789"),
    ("Cudzoziemiec, karta pobytu AB1234567, przebywa legalnie.", "AB1234567"),
    ("Recepta o numerze 0103000012345678901234 zostala zrealizowana.",
     "0103000012345678901234"),
    ("Dzialka ewidencyjna 146501_1.0001.123/4 o powierzchni 0,25 ha.",
     "146501_1.0001.123/4"),
])
def test_numer_znika_z_dokumentu(zdanie, numer, konfig):
    assert numer not in wytnij(zdanie, konfig)


def test_nazwisko_znika(konfig):
    czysty = wytnij("Wniosek zlozyla Katarzyna Zielinska z Opola.", konfig)
    assert "Zielinska" not in czysty and "Katarzyna" not in czysty


# --- Czego wycinac NIE wolno: falszywe alarmy psuja dokument ---

@pytest.mark.parametrize("zdanie, zostaje", [
    ("Kwota dotacji wyniosla 152 422 384,00 zl w tym roku.", "152 422 384"),
    ("Umowe zawarto w dniu 05.05.2016 roku.", "05.05.2016"),
    ("Sprawa o sygnaturze 1331.35.2020 zostala zakonczona.", "1331.35.2020"),
    ("Program realizowany w latach 2015-2030 przez gmine.", "2015-2030"),
    ("Wydatki wyniosly 8 113 087 zlotych w calym okresie.", "8 113 087"),
])
def test_nie_ruszamy_kwot_i_dat(zdanie, zostaje, konfig):
    assert zostaje in wytnij(zdanie, konfig)


# --- Odwracalnosc: bez tego narzedzie jest bezuzyteczne ---

def test_da_sie_wrocic_do_oryginalu(konfig):
    tekst = ("Pan Jan Kowalski, PESEL 85010112345, tel. 601 234 567, "
             "NIP 5260250274, mieszka w Opolu.")
    trafienia = A.znajdz(tekst, konfig)
    czysty, slownik = A.podmien(tekst, trafienia)
    odtworzony = czysty
    for etykieta, prawdziwe in slownik.items():
        odtworzony = odtworzony.replace(etykieta, prawdziwe)
    assert odtworzony == tekst


def test_etykiety_sa_ponumerowane(konfig):
    tekst = "Spotkali sie Jan Kowalski oraz Anna Nowak w sprawie umowy."
    czysty, slownik = A.podmien(tekst, A.znajdz(tekst, konfig))
    assert "[OSOBA_1]" in czysty and "[OSOBA_2]" in czysty
    assert len(set(slownik.values())) == len(slownik)
