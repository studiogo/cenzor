#!/usr/bin/env python3
"""Wycina dane osobowe z tekstu przed wyslaniem do modelu w chmurze.

Znajduje nazwiska, firmy, miejsca, maile, telefony, klucze — takze te,
ktorych nie ma na zadnej liscie — i podmienia je na etykiety typu [OSOBA_1].
Slownik podmian zostaje na dysku, wiec zamiane da sie odwrocic.
"""
import argparse, json, os, re, sys
from pathlib import Path

KATALOG = Path(__file__).resolve().parent.parent
KONFIG = KATALOG / "konfiguracja.json"
KONFIG_LOKALNA = KATALOG / "konfiguracja.lokalna.json"   # Twoje wlasne ustawienia, poza repozytorium

DOMYSLNA_KONFIG = {
    "encje": ["PERSON", "ORGANIZATION", "LOCATION", "EMAIL_ADDRESS", "PHONE_NUMBER",
              "CREDIT_CARD", "IP_ADDRESS", "US_SSN", "US_ITIN", "US_PASSPORT",
              "US_DRIVER_LICENSE", "US_BANK_NUMBER", "IBAN_CODE", "MEDICAL_LICENSE",
              "UK_NHS", "CRYPTO", "MAC_ADDRESS", "URL"],
    "nie_ruszaj": ["Sp. z o.o.", "S.A.", "Urzad Miasta", "Ministerstwo",
                   "API", "CRM", "RODO"],
    "prog_pewnosci": 0.4,
    "jezyk": "en"
}

# spaCy nazywa encje po polsku (persName, orgName), Presidio szuka angielskich nazw.
# Bez tego tlumaczenia polskie nazwiska i firmy przepadaja.
MAPA_ENCJI = {
    "PERSON": "PERSON", "persName": "PERSON",
    "ORG": "ORGANIZATION", "orgName": "ORGANIZATION",
    "LOC": "LOCATION", "GPE": "LOCATION", "FAC": "LOCATION",
    "placeName": "LOCATION", "geogName": "LOCATION",
    "NORP": "NRP", "DATE": "DATE_TIME", "TIME": "DATE_TIME", "date": "DATE_TIME", "time": "DATE_TIME",
    "AGE": "AGE", "ID": "ID", "EMAIL": "EMAIL_ADDRESS",
}

ETYKIETY = {
    "PERSON": "OSOBA", "ORGANIZATION": "FIRMA", "ORG": "FIRMA", "LOCATION": "MIEJSCE", "GPE": "MIEJSCE",
    "EMAIL_ADDRESS": "MAIL", "PHONE_NUMBER": "TELEFON", "PHONE_KOTWICA": "TELEFON", "CREDIT_CARD": "KARTA",
    "IP_ADDRESS": "IP", "US_SSN": "PESEL", "IBAN_CODE": "KONTO", "URL": "ADRES", "US_ITIN": "ID_PODATKOWE",
    "US_PASSPORT": "PASZPORT", "US_DRIVER_LICENSE": "PRAWO_JAZDY",
    "US_BANK_NUMBER": "KONTO", "MEDICAL_LICENSE": "LICENCJA_MED",
    "UK_NHS": "ID_MEDYCZNE", "CRYPTO": "PORTFEL", "MAC_ADDRESS": "MAC", "AGE": "WIEK",
    "DATE_TIME": "DATA", "NRP": "NARODOWOSC", "KLUCZ_API": "KLUCZ",
    "PL_PESEL": "PESEL", "PL_NIP": "NIP", "PL_REGON": "REGON", "PL_DOWOD": "DOWOD",
    "PL_KOD": "KOD", "PL_KRS": "KRS", "PL_REJ": "NR_REJ",
    "PL_PASZPORT": "PASZPORT", "PL_KW": "KSIEGA_WIECZYSTA",
    "PL_PWZ": "PWZ_LEKARZA", "PL_PRAWO_JAZDY": "PRAWO_JAZDY", "PL_ARIMR": "NR_PRODUCENTA",
    "PL_BDO": "BDO", "PL_VIN": "VIN", "IMEI": "IMEI", "PL_KARTA_POBYTU": "KARTA_POBYTU",
    "PL_RECEPTA": "RECEPTA", "PL_DZIALKA": "DZIALKA",
}

WZORCE_WLASNE = [
    ("KLUCZ_API", re.compile(r"\b(?:acc|sk|pk|ghp|xox[baprs])[-_][A-Za-z0-9_-]{16,}\b")),
    ("KLUCZ_API", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b")),
    # Polskie identyfikatory. Presidio zna tylko PESEL — reszty pilnujemy sami.
    # NIP i REGON maja sume kontrolna, wiec sprawdzamy ja nizej (SPRAWDZ_SUME).
    ("PL_NIP", re.compile(r"\bNIP[:\s]*((?:[0-9][ .-]?){9}[0-9])", re.I)),
    ("PL_NIP", re.compile(r"(?<![0-9])([0-9]{3}-[0-9]{2}-[0-9]{2}-[0-9]{3}|[0-9]{3}-[0-9]{3}-[0-9]{2}-[0-9]{2})(?![0-9])")),
    ("PL_REGON", re.compile(r"\bREGON[:\s]*([0-9]{9}|[0-9]{14})\b", re.I)),
    # goly ciag cyfr bez etykiety — chroni nas suma kontrolna, nie kontekst
    ("PL_NIP", re.compile(r"(?<![0-9-])([0-9]{10})(?![0-9-])")),
    ("PL_REGON", re.compile(r"(?<![0-9-])([0-9]{9}|[0-9]{14})(?![0-9-])")),
    ("PL_KRS", re.compile(r"\bKRS[:\s]*([0-9]{6,10})\b", re.I)),
    # KRS bez slowa "KRS" obok: dziesiec cyfr z wiodacymi zerami ("pod nr 0000713345").
    # Kwoty i lata nie zaczynaja sie od zer, wiec falszywe trafienie jest malo prawdopodobne.
    ("PL_KRS", re.compile(r"(?<![0-9-])(0{3}[0-9]{7})(?![0-9-])")),
    # Paszport: dwie litery i siedem cyfr, z suma kontrolna (SPRAWDZ_SUME).
    ("PL_PASZPORT", re.compile(r"\b([A-Z]{2}\s?[0-9]{7})\b")),
    # Ksiega wieczysta: kod wydzialu, osiem cyfr, cyfra kontrolna.
    ("PL_KW", re.compile(r"\b([A-Z]{2}[0-9A-Z]{2}\s?/\s?[0-9]{8}\s?/\s?[0-9])\b")),
    # Prawo wykonywania zawodu lekarza: siedem cyfr, pierwsza jest kontrolna (NIL).
    ("PL_PWZ", re.compile(r"\b([1-9][0-9]{6})\b")),
    # IMEI telefonu: pietnascie cyfr, algorytm Luhna.
    ("IMEI", re.compile(r"\b([0-9]{15})\b")),
    # Numer recepty: 22 cyfry (Narodowy Fundusz Zdrowia). Ciag tej dlugosci
    # nie wystepuje w tekscie przypadkiem, wiec kotwica nie jest potrzebna.
    ("PL_RECEPTA", re.compile(r"\b([0-9]{22})\b")),
    # Identyfikator dzialki ewidencyjnej: kod TERYT gminy, numer obrebu, numer
    # dzialki — np. 146501_1.0001.123. Ksztalt sam w sobie jest jednoznaczny.
    ("PL_DZIALKA", re.compile(r"\b([0-9]{6}_[0-9]\.[0-9]{4}\.[0-9]+(?:/[0-9]+)?)\b")),
    # Ponizsze nie maja sumy kontrolnej, wiec wymagaja slowa-kotwicy obok.
    # Bez niej kazda liczba tej dlugosci bylaby falszywym trafieniem.
    ("PL_VIN", re.compile(r"(?:VIN|nr\s*nadwozia|numer\s*nadwozia)[^A-Z0-9\n]{0,8}([A-HJ-NPR-Z0-9]{17})\b", re.I)),
    ("PL_PRAWO_JAZDY", re.compile(r"(?:praw[oa]\s*jazdy)[^0-9\n]{0,20}([0-9]{9}|[0-9]{11}|[0-9]{14})\b", re.I)),
    ("PL_ARIMR", re.compile(r"(?:producenta|ewidencji\s*producent\w*|numer\s*EP)[^0-9\n]{0,20}([0-9]{9})\b", re.I)),
    ("PL_BDO", re.compile(r"(?:BDO)[^0-9\n]{0,12}([0-9]{9})\b", re.I)),
    ("PL_KARTA_POBYTU", re.compile(r"(?:kart[ayę]\s*pobytu)[^A-Z0-9\n]{0,20}([A-Z]{2}\s?[0-9]{7})\b", re.I)),
    ("PL_DOWOD", re.compile(r"\b[A-Z]{3}\s?[0-9]{6}\b")),
    ("PL_REJ", re.compile(r"\b[A-Z]{2,3}\s?(?=[0-9A-Z]{4,5}\b)(?=[0-9A-Z]*[0-9])[0-9A-Z]{4,5}\b")),
    ("PL_KOD", re.compile(r"(?<![0-9-])[0-9]{2}-[0-9]{3}(?![0-9-])")),
    # Telefony. Goly ciag cyfr NIE wystarczy: kwota "5 898 310" i data "05.05.2016"
    # wygladaja tak samo jak numer. Na 463 podmianach oznaczonych jako telefon
    # w pismach urzedowych tylko 32 stały przy slowie "tel" — reszta to byly kwoty,
    # daty i sygnatury spraw (pomiar 4 wrzesnia 2026). Dlatego wymagamy przedrostka
    # +48 albo slowa-kotwicy obok (wzorzec PHONE_KOTWICA nizej).
    # Cena: goly numer wypisany bez zadnego opisu przechodzi.
    ("PHONE_NUMBER", re.compile(r"\+48[\s-]{0,3}(?:\(\d{2,3}\)|\d{2,3})[\s-]{0,3}\d{3}[\s-]{0,3}\d{2,3}(?:[\s-]{0,3}\d{2,3})?(?![0-9])")),
    # numer po slowie "tel"/"fax" — lapie tez stary zapis miejski 441-23-70
    # Numer po slowie "tel"/"fax". Odstep krotki i BEZ konca wiersza: w tabeli
    # dluga przerwa przeskakiwala przez cala kolumne do liczby z innego wiersza.
    ("PHONE_KOTWICA", re.compile(r"(?:tel\.?|telefon\w*|fax|faks|kom\.?)[^0-9\n]{0,12}((?:[0-9][ ()-]{0,2}){6,12}[0-9])", re.I)),
    ("IBAN_CODE", re.compile(r"\b(?:PL[\s-]?)?[0-9]{2}(?:[\s-]?[0-9]{4}){6}\b")),
]

PLIK_IMION = KATALOG / "pomiar" / "imiona.txt"


def wzorzec_imion():
    """Imie z listy to pewny sygnal osoby — nawet gdy tabela rozbila je od nazwiska.
    Lapiemy imie i, jesli zaraz po nim stoi wyraz z wielkiej litery, takze jego.
    """
    if not PLIK_IMION.exists():
        return None
    imiona = sorted({w for w in PLIK_IMION.read_text(encoding="utf-8").split() if w}, key=len, reverse=True)
    # odmiana: Janem, Annie, Piotrowi — dopuszczamy koncowke przypadku
    trzon = "|".join(re.escape(i[:-1] if len(i) > 4 else i) for i in imiona)
    return re.compile(rf"\b(?:{trzon})[a-ząćęłńóśźż]{{0,4}}(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\-]{{2,}})?\b")


_IMIONA = wzorzec_imion()
if _IMIONA is not None:
    WZORCE_WLASNE.append(("PERSON", _IMIONA))


# Typy, ktore maja sume kontrolna — odrzucamy trafienie, ktore jej nie przechodzi.
def _suma_nip(c):
    c = re.sub(r"\D", "", c)
    if len(c) != 10:
        return False
    w = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    return sum(int(c[i]) * w[i] for i in range(9)) % 11 == int(c[9])


def _suma_regon(c):
    c = re.sub(r"\D", "", c)
    if len(c) == 9:
        w = [8, 9, 2, 3, 4, 5, 6, 7]
    elif len(c) == 14:
        w = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
    else:
        return False
    s = sum(int(c[i]) * w[i] for i in range(len(w))) % 11
    return (0 if s == 10 else s) == int(c[-1])


def _suma_pesel(c):
    c = re.sub(r"\D", "", c)
    if len(c) != 11:
        return False
    w = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    return (10 - sum(int(c[i]) * w[i] for i in range(10)) % 10) % 10 == int(c[10])


def _suma_paszport(c):
    """Dwie litery i siedem cyfr. Litery licza sie jako 10 dla A, 11 dla B i dalej.
    Wagi 7,3,9,1,7,3,1,7,3; reszta z dzielenia sumy przez 10 musi wyjsc zero."""
    c = re.sub(r"[^A-Za-z0-9]", "", c).upper()
    if len(c) != 9 or not c[:2].isalpha() or not c[2:].isdigit():
        return False
    w = [7, 3, 9, 1, 7, 3, 1, 7, 3]
    wartosci = [ord(z) - 55 if z.isalpha() else int(z) for z in c]
    return sum(a * b for a, b in zip(wartosci, w)) % 10 == 0


def _suma_kw(c):
    """Numer ksiegi wieczystej: KOD/00000000/C. Wagi 1,3,7 w kolko, modulo 10.
    Cyfry licza sie same, litery od A=10, X=33, Y=34, Z=35."""
    c = re.sub(r"\s", "", c).upper()
    czesci = c.split("/")
    if len(czesci) != 3 or len(czesci[0]) != 4 or len(czesci[1]) != 8 or len(czesci[2]) != 1:
        return False
    # Tabela wartosci znakow z dokumentacji ksiag wieczystych: cyfry same za siebie,
    # potem X=10 i litery od A=11, z pominieciem Q i V.
    LITERY = "XABCDEFGHIJKLMNOPRSTUWYZ"
    znaki = czesci[0] + czesci[1]
    w = [1, 3, 7]
    suma = 0
    for i, z in enumerate(znaki):
        if z.isdigit():
            wartosc = int(z)
        elif z in LITERY:
            wartosc = 10 + LITERY.index(z)
        else:
            return False
        suma += wartosc * w[i % 3]
    return suma % 10 == int(czesci[2])


def _telefon_dziewiec_cyfr(c):
    """Polski numer ma dziewiec cyfr. Bez tego sprawdzenia wzorzec bierze kwote
    "15 422 384" za telefon — a w pismach budzetowych takich kwot sa setki.
    Numer poprzedzony slowem "tel" ma wlasny typ i tego progu nie przechodzi,
    bo stare numery miejskie bywaja krotsze."""
    if "." in c:
        return False          # "05.05.2016", "1331.35.2020" — data albo sygnatura
    if re.search(r"\s\s", c):
        return False          # "05   1 470 132" — numer wiersza i kwota z sasiedniej kolumny
    c = re.sub(r"\D", "", c)
    if c.startswith("48") and len(c) == 11:
        c = c[2:]
    return len(c) == 9 and c[0] != "0"   # polski numer nie zaczyna sie od zera


def _telefon_z_kotwica(c):
    """Numer przy slowie "tel" ma miec od siedmiu do jedenastu cyfr i zadnej kropki.
    Bez tego wzorzec bral z tabeli kwote stojaca obok."""
    if "." in c:
        return False
    return 7 <= len(re.sub(r"\D", "", c)) <= 11


def _suma_pwz(c):
    """Numer prawa wykonywania zawodu lekarza: siedem cyfr, pierwsza kontrolna.
    Reszta to szesc cyfr mnozonych przez wagi 1-6, modulo 11 (zasady Naczelnej
    Izby Lekarskiej). Numer nie zaczyna sie od zera."""
    c = re.sub(r"\D", "", c)
    if len(c) != 7 or c[0] == "0":
        return False
    return sum(int(c[i + 1]) * (i + 1) for i in range(6)) % 11 == int(c[0])


def _luhn(c):
    """Algorytm Luhna — sprawdza IMEI telefonu."""
    c = re.sub(r"\D", "", c)
    if len(c) != 15:
        return False
    suma = 0
    for i, z in enumerate(reversed(c)):
        n = int(z)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        suma += n
    return suma % 10 == 0


SPRAWDZ_SUME = {"PL_PWZ": _suma_pwz, "IMEI": _luhn, "PL_NIP": _suma_nip, "PL_REGON": _suma_regon, "PL_PESEL": _suma_pesel,
                "PHONE_NUMBER": _telefon_dziewiec_cyfr, "PHONE_KOTWICA": _telefon_z_kotwica,
                "PL_PASZPORT": _suma_paszport, "PL_KW": _suma_kw}


def wczytaj_konfig():
    """Kolejnosc: ustawienia wbudowane, potem plik w skillu, na koncu Twoj wlasny.
    Nazwy klientow trzymaj w konfiguracja.lokalna.json — ten plik nie trafia
    do repozytorium, wiec nie opublikujesz ich przez przypadek."""
    konfig = dict(DOMYSLNA_KONFIG)
    for plik in (KONFIG, KONFIG_LOKALNA):
        if plik.exists():
            dane = json.loads(plik.read_text(encoding="utf-8"))
            if plik is KONFIG_LOKALNA and isinstance(dane.get("nie_ruszaj"), list):
                # lokalne nazwy DOPISUJEMY, nie zastepujemy nimi listy z repozytorium
                dane = {**dane, "nie_ruszaj": konfig["nie_ruszaj"] + dane["nie_ruszaj"]}
            konfig.update({k: v for k, v in dane.items() if not k.startswith("_")})
    if not KONFIG.exists():
        KONFIG.write_text(json.dumps(DOMYSLNA_KONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    return konfig


def zbuduj_silnik(jezyk):
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    modele = {"en": "en_core_web_lg", "pl": "pl_core_news_lg"}
    if jezyk not in modele:
        sys.exit(f"Nieznany jezyk: {jezyk}. Dostepne: {', '.join(modele)}")
    import spacy.util
    if modele[jezyk] not in spacy.util.get_installed_models():
        sys.exit(f"Brak modelu jezykowego {modele[jezyk]}. Zainstaluj:\n"
                 f"  {sys.executable} -m spacy download {modele[jezyk]}\n"
                 f"Bez niego nazwiska i firmy NIE zostana wyciete.")
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": jezyk, "model_name": modele[jezyk]}],
        "ner_model_configuration": {"model_to_presidio_entity_mapping": MAPA_ENCJI},
    })
    return AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=[jezyk])


def sklej_uklad(tekst):
    """PDF z tabeli lamie nazwy i numery w polowie: "77-\\n    441-23-70".
    Krotka przerwa (zawiniety wiersz) staje sie spacja — nazwa znow jest calascia.
    Dluga przerwa to granica kolumny w tabeli: zostaje separatorem, zeby model
    nie sklejal dwoch sasiednich komorek w jedno zdanie.
    Mapa zwraca pozycje z powrotem na oryginal, wiec odwrocenie dziala 1:1.
    """
    PROG = 4  # tyle bialych znakow juz oznacza granice kolumny, nie zawiniety wiersz
    czesci, mapa, i, n = [], [], 0, len(tekst)
    while i < n:
        if tekst[i].isspace():
            j = i
            while j < n and tekst[j].isspace():
                j += 1
            zastapienie = " " if (j - i) < PROG else " | "
            for z in zastapienie:
                czesci.append(z)
                mapa.append(i)
            i = j
        else:
            czesci.append(tekst[i])
            mapa.append(i)
            i += 1
    mapa.append(n)
    return "".join(czesci), mapa


def znajdz(tekst_oryginalny, konfig):
    """Zwraca liste (poczatek, koniec, typ, fragment), bez nakladania sie."""
    tekst, mapa = sklej_uklad(tekst_oryginalny)
    silnik = zbuduj_silnik(konfig["jezyk"])
    obslugiwane = set(silnik.get_supported_entities(language=konfig["jezyk"]))
    chciane = [e for e in konfig["encje"] if e in obslugiwane]
    pominiete = [e for e in konfig["encje"] if e not in obslugiwane]
    if pominiete:
        print(f"Uwaga: silnik nie zna tych typow, pomijam: {', '.join(pominiete)}", file=sys.stderr)
    wyniki = silnik.analyze(text=tekst, language=konfig["jezyk"],
                            entities=chciane,
                            score_threshold=konfig["prog_pewnosci"])
    trafienia = []
    for w in wyniki:
        sprawdz = SPRAWDZ_SUME.get(w.entity_type)
        if sprawdz and not sprawdz(tekst[w.start:w.end]):
            continue          # silnik bierze daty i sygnatury za telefon
        trafienia.append((w.start, w.end, w.entity_type, 1))
    for typ, wzor in WZORCE_WLASNE:
        # jesli wzorzec ma grupe, wycinamy sama wartosc — slowo "NIP" ma zostac w tekscie
        g = 1 if wzor.groups else 0
        for m in wzor.finditer(tekst):
            sprawdz = SPRAWDZ_SUME.get(typ)
            if sprawdz and not sprawdz(m.group(g)):
                continue
            trafienia.append((m.start(g), m.end(g), typ, 0))

    biale = {b.lower() for b in konfig["nie_ruszaj"]}
    # najpierw wlasne wzorce (t[3]==0), potem dluzsze trafienia
    trafienia.sort(key=lambda t: (t[3], t[0], -(t[1] - t[0])))
    czyste, zajete = [], []
    for p, k, typ, _ in trafienia:
        if any(p < kk and pp < k for pp, kk in zajete):
            continue
        fragment = tekst[p:k]
        if fragment.lower() in biale or fragment.strip() == "":
            continue
        # pozycje z tekstu sklejonego wracaja na oryginal
        po, ko = mapa[p], mapa[k]
        czyste.append((po, ko, typ, tekst_oryginalny[po:ko]))
        zajete.append((p, k))

    # Raz uznane za osobe — zawsze wycinane. Tabela potrafi oddzielic nazwisko
    # od imienia, wiec samotne "Sokolowskiej" nizej w dokumencie tez ma zniknac.
    nazwy = set()
    for _, _, typ, fragment in czyste:
        if ETYKIETY.get(typ) != "OSOBA":
            continue
        for czlon in fragment.split():
            czlon = czlon.strip(".,;:()\"„”'")
            if len(czlon) > 3 and czlon[0].isupper():
                nazwy.add(czlon)
    if nazwy:
        wzor = re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, nazwy), key=len, reverse=True)) + r")\b")
        for m in wzor.finditer(tekst_oryginalny):
            if not any(p2 < m.end() and m.start() < k2 for p2, k2, _, _ in czyste):
                czyste.append((m.start(), m.end(), "PERSON", m.group()))

    czyste.sort(key=lambda t: t[0])
    return czyste


def podmien(tekst, trafienia):
    slownik, licznik, czesci, ostatni = {}, {}, [], 0
    for p, k, typ, fragment in trafienia:
        etykieta = ETYKIETY.get(typ, typ)
        istniejaca = next((e for e, o in slownik.items() if o == fragment), None)
        if istniejaca is None:
            licznik[etykieta] = licznik.get(etykieta, 0) + 1
            istniejaca = f"[{etykieta}_{licznik[etykieta]}]"
            slownik[istniejaca] = fragment
        czesci.append(tekst[ostatni:p])
        czesci.append(istniejaca)
        ostatni = k
    czesci.append(tekst[ostatni:])
    return "".join(czesci), slownik


def konsola_utf8():
    """Windows zapisuje wyjscie przekierowane do pliku w kodowaniu cp1250 — polskie
    litery w nazwisku albo w sciezce wywracaja wtedy program. Wymuszamy UTF-8.
    Na Macu i Linuksie to nic nie zmienia."""
    for strumien in (sys.stdout, sys.stderr):
        if hasattr(strumien, "reconfigure"):
            strumien.reconfigure(encoding="utf-8", errors="replace")


def zabezpiecz(plik):
    """Slownik ma czytac tylko jego wlasciciel.
    Mac i Linux: prawa 600. Windows nie zna takich praw — tam odcinamy
    uprawnienia dziedziczone z katalogu i zostawiamy dostep tylko zalogowanemu
    uzytkownikowi (icacls). Gdy sie nie uda, mowimy o tym, zamiast udawac."""
    if os.name != "nt":
        os.chmod(plik, 0o600)
        return
    import subprocess
    uzytkownik = os.environ.get("USERNAME")
    if not uzytkownik:
        print("Uwaga: nie znam nazwy uzytkownika, slownik ma zwykle uprawnienia.", file=sys.stderr)
        return
    wynik = subprocess.run(["icacls", str(plik), "/inheritance:r", "/grant:r", f"{uzytkownik}:F"],
                           capture_output=True)
    if wynik.returncode != 0:
        print("Uwaga: nie udalo sie ograniczyc dostepu do slownika tylko do Ciebie.", file=sys.stderr)


def main():
    konsola_utf8()
    p = argparse.ArgumentParser(description="Wycina dane osobowe z pliku tekstowego.")
    p.add_argument("plik", help="plik wejsciowy")
    p.add_argument("-o", "--wyjscie", help="plik wynikowy (domyslnie <nazwa>-anon.txt)")
    p.add_argument("--jezyk", choices=["en", "pl"], help="jezyk tekstu (domyslnie z konfiguracji)")
    p.add_argument("--podglad", action="store_true", help="tylko pokaz, co zostaloby wyciete")
    args = p.parse_args()

    zrodlo = Path(args.plik)
    if not zrodlo.exists():
        sys.exit(f"Nie ma pliku: {zrodlo}")

    konfig = wczytaj_konfig()
    if args.jezyk:
        konfig["jezyk"] = args.jezyk

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from wczytaj import wczytaj, BladOdczytu
    try:
        tekst, format_pliku = wczytaj(zrodlo)
    except BladOdczytu as e:
        sys.exit(str(e))
    if format_pliku != "txt":
        print(f"Wczytano {format_pliku.upper()}: {len(tekst.split())} slow.")
    trafienia = znajdz(tekst, konfig)

    if args.podglad:
        widziane = {}
        for _, _, typ, fragment in trafienia:
            widziane.setdefault((ETYKIETY.get(typ, typ), fragment), 0)
            widziane[(ETYKIETY.get(typ, typ), fragment)] += 1
        print(f"Znaleziono {len(trafienia)} wystapien, {len(widziane)} roznych:\n")
        for (etykieta, fragment), ile in sorted(widziane.items()):
            print(f"  {etykieta:12} {fragment[:60]:62} x{ile}")
        print("\nNic nie zapisano. Uruchom bez --podglad, zeby wyciac.")
        return

    czysty, slownik = podmien(tekst, trafienia)
    domyslne = zrodlo.with_name(zrodlo.stem + "-anon" + (zrodlo.suffix if format_pliku == "txt" else ".txt"))
    wyjscie = Path(args.wyjscie) if args.wyjscie else domyslne
    plik_slownika = wyjscie.with_name(wyjscie.stem + "-slownik.json")

    wyjscie.write_text(czysty, encoding="utf-8")
    plik_slownika.write_text(json.dumps(slownik, ensure_ascii=False, indent=2), encoding="utf-8")
    zabezpiecz(plik_slownika)

    print(f"Wyciete: {len(trafienia)} wystapien, {len(slownik)} roznych rzeczy.")
    print(f"Do wyslania: {wyjscie}")
    print(f"Slownik (zostaje u Ciebie): {plik_slownika}")


if __name__ == "__main__":
    main()
