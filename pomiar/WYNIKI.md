# Wyniki pomiaru — 4 wrzesnia 2026

Jezyk: polski. Dwa niezalezne poligony, **324 057 slow** lacznie.
Dokumentow nie ma w repozytorium — pobiera je `pobierz.py` z adresow w `ZRODLA.md`
i `ZRODLA-poligon2.md`.

- **Poligon 1** (97 082 slowa): pisma przetargowe, uchwaly sejmiku, sprawozdania
  z wspolpracy z organizacjami. Na nim narzedzie bylo strojone.
- **Poligon 2** (226 975 slow): wystapienia pokontrolne NIK, sprawozdania budzetowe,
  umowy dotacji, uchwaly zarzadow wojewodztw. **Zebrany po zakonczeniu strojenia** —
  narzedzie nie widzialo tych dokumentow, gdy powstawaly jego reguly.

## Skutecznosc wycinania

| kategoria | poligon 1 | poligon 2 |
|---|---|---|
| PESEL / NIP / REGON | 100% (15) | 100% (6) |
| numer konta | 100% (1) | 100% (4) |
| adres e-mail | 100% (13) | 100% (2) |
| telefon | 100% (9) | brak w dokumentach |
| kod pocztowy | 100% (30) | 100% (13) |
| osoby | 100% (95) | 100% (122) |
| firmy | 100% (40) | 100% (77) |
| organizacje | 96,0% (303) | 97,2% (71) |

W nawiasach liczba wystapien w dokumentach. Odwracalnosc: **10 z 10** na obu
poligonach, tekst odtworzony co do znaku.

## Pomiar kontrolny — bez wlasnej listy imion

`pomiar.py` szuka osob po liscie imion, ktorej uzywa tez anonimizacja. Zeby nie
mierzyc wlasnym przyrzadem, `kontrola.py` buduje liste prawdy inaczej: pyta
model spaCy, co na oryginale uznaje za osobe. Podaje dwie liczby.

| wskaznik | poligon 1 | poligon 2 |
|---|---|---|
| pelne nazwiska (imie + nazwisko) | 99,1% (106) | 98,9% (181) |
| wszystko, co model wzial za osobe | 91,6% (179) | 84,2% (380) |

Rozjazd miedzy wierszami bierze sie stad, ze model oznacza jako osobe rowniez
nazwy ulic ("Krasinskiego", "Popieluszki"), przymiotniki od nazw powiatow
("Mazowiecki", "Pultuskiego") i wyrazy urwane przez lamanie w PDF ("Departamen",
"jacego"). To nie sa dane osobowe. Wskaznik ostry liczy tylko dwuczlonowe
"imie + nazwisko" i on odpowiada na pytanie, ktore naprawde zadajemy.

Przez oba poligony przeszlo **jedno prawdziwe nazwisko** — "Estera Wilczynska"
w sprawozdaniu budzetowym gminy Ozimek, na 287 pelnych nazwisk lacznie.
Dwa pozostale trafienia wskaznika ostrego to "B I P SUW" i "Malinowej Wiacie",
czyli nie nazwiska.

**Do cytowania publicznie: 98,9% na dokumentach, ktorych narzedzie nie widzialo
w czasie strojenia.** Wskaznik szeroki podajemy obok, zeby bylo jasne, ile
w nim szumu.

## Czego to nie zalatwia

1. **Nazwisko oddzielone od imienia granica komorki w tabeli.** Gdy PDF stawia
   imie w jednym wierszu, a nazwisko w nastepnym, samotne nazwisko potrafi przejsc.
2. **Rozpoznanie po kontekscie.** Wyciecie nazwisk nie chroni przed ustaleniem,
   o kogo chodzi. W protokole sesji rady gminy nazwa gminy padla 56 razy;
   po anonimizacji zostala dwa razy — a jedno wystarczy, by "Wojt [OSOBA_4]"
   mial tylko jedna mozliwa wartosc.
3. **Jeden byt, wiele etykiet.** Ta sama instytucja w roznych odmianach
   ("Rada", "Rady Gminy", "Rada Gminy Wapno") dostaje rozne numery.
4. **Dane pacjentow i rejestry medyczne** — tych nie anonimizujemy, tylko
   nie wyjmujemy z systemu klienta.

## Jak powtorzyc pomiar

    python3 pomiar/pobierz.py poligon      # sciaga dokumenty z BIP-ow
    python3 pomiar/pomiar.py poligon       # miara glowna
    python3 pomiar/kontrola.py poligon     # miara niezalezna od listy imion

Bez pobierania czegokolwiek dzialaja sztuczne przyklady z `pomiar/przyklady/`.
Numery PESEL, NIP i REGON sa w nich wygenerowane z poprawna suma kontrolna
i nie naleza do nikogo.


## Pomiar trzeci — 4 wrzesnia 2026, po naprawach

Ten sam przyrzad, 19 dokumentow z obu poligonow (dokument 05 pominiety: serwer
PARP oddaje uszkodzony PDF). Zmiany od poprzedniego pomiaru: dopisany paszport
i ksiega wieczysta z sumami kontrolnymi, KRS rozpoznawany bez slowa "KRS" obok,
zawezone wykrywanie telefonu.

| wskaznik | nasze | Parawan 0.x (4 wrzesnia) |
|---|---|---|
| pelne nazwiska, 286 sztuk | 99,0% (przeszly 3) | 82,5% (przeszlo 50) |
| wszystko, co model uznal za osobe, 556 | 86,3% | 48,7% |

Z naszych trzech tylko "Estera Wilczynska" jest nazwiskiem; "B I P SUW"
i "Malinowej Wiacie" to pomylki modelu. U Parawana wsrod 50 sa prawdziwe osoby.

### Falszywe alarmy telefonu

Przed naprawa: 463 podmiany oznaczone jako telefon, z czego przy slowie "tel",
"fax" albo "kom" stalo 32. Reszta to daty ("05.05.2016"), kwoty ("5 898 310"),
sygnatury spraw ("1331.35.2020") i pociete numery kont.
Po naprawie: 19 podmian, okolo polowa to prawdziwe numery. Reszta to
dziewieciocyfrowe kwoty, ktorych bez kontekstu nie da sie odroznic od numeru.

Nadmiar wycinania nie jest wyciekiem, ale psuje wynik: model dostaje sprawozdanie
budzetowe, w ktorym kwoty zamieniono na etykiety.


## Pomiar czwarty — cudzy korpus, adnotacja ludzka (4 wrzesnia 2026)

Zarzut, ktory mozna postawic pomiarom wyzej: liste prawdy buduje model spaCy,
a tego samego modelu uzywa anonimizacja. Dlatego ten pomiar idzie na korpusie,
w ktorym nazwiska oznaczyli ludzie: **KPWr — Korpus Jezyka Polskiego Politechniki
Wroclawskiej**, czesc testowa, licencja CC BY 3.0
(https://huggingface.co/datasets/clarin-pl/kpwr-ner).

Material zupelnie inny niz nasz poligon: blogi i teksty prasowe zamiast pism
urzedowych. 75 696 slow, 949 oznaczen osob, 642 rozne.

| wskaznik | wynik |
|---|---|
| pelne nazwiska (dwa czlony), 373 rozne | 98,1% wycietych (przeszlo 7) |
| wszystkie oznaczenia osob, 642 rozne | 94,5% wycietych (przeszlo 35) |

Co przeszlo: nazwiska obce, ktorych model polskiego nie rozpoznaje ("Cab Calloway",
"Eberhard Schlicker"), oraz pseudonimy i przezwiska, ktore czlowiek slusznie
oznaczyl jako osoby, ale nazwiskami nie sa ("HenkvD", "Ciacho", "Kali", "Cesarz").

Powtorzenie: `pomiar/korpus.py` po pobraniu pliku
`data/kpwr-ner-n82-test.iob` z adresu wyzej.

## Sprawdzian numerow (4 wrzesnia 2026)

Prawdziwych numerow PESEL czy paszportu nikt nie publikuje i slusznie, wiec
tutaj numery sa budowane: kazdy z policzona cyfra kontrolna, wlozony w zdanie
takie, jakie spotyka sie w pismach. Skrypt: `pomiar/numery.py`.

**Wykryte: 23 z 23 rodzajow.** PESEL, NIP, REGON, paszport, numer lekarza, IMEI,
ksiega wieczysta, KRS (ze slowem i bez), dowod osobisty, kod pocztowy, konto,
telefon (z kotwica i z +48), e-mail, VIN, prawo jazdy, numer producenta rolnego,
BDO, karta pobytu, recepta, dzialka ewidencyjna, numer rejestracyjny.

**Falszywe alarmy na 323 667 slowach pism urzedowych, w ktorych tych numerow nie ma:**
jeden IMEI (przypadkowy ciag pietnastu cyfr przechodzacy algorytm Luhna).
Pozostale jedenascie rodzajow: zero.
