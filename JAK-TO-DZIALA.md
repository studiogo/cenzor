# Jak to dziala

Narzedzie wycina dane osobowe z dokumentu, zanim wyslesz go do modelu w chmurze.
Dziala w calosci na Twoim komputerze.

## Co z czego powstaje

Z jednego dokumentu powstaja **dwa pliki**. Jeden wysylasz, drugi zostaje u Ciebie.

```
  TWOJ DOKUMENT
  "Umowa z Janem Kowalskim, PESEL 85010112345"
            |
            v
      [1] ... [5]   <-- przetwarzanie na Twoim komputerze
            |
      +-----+--------------------------------------+
      v                                            v
  PLIK OCZYSZCZONY                          PLIK Z KLUCZEM
  umowa-anon.txt                            umowa-anon-slownik.json

  "Umowa z [OSOBA_1],                       [OSOBA_1] = Jan Kowalski
   PESEL [PESEL_1]"                         [PESEL_1] = 85010112345

  TEN WYSYLASZ do ChatGPT,                  TEN ZOSTAJE NA TWOIM DYSKU.
  Claude albo innego modelu.                Nie wysylaj go nigdzie.
  Nie ma w nim zadnych                      Razem z pierwszym plikiem
  danych osobowych.                         odtwarza caly oryginal.
      |                                            |
      v                                            |
  odpowiedz modelu                                 |
  "[OSOBA_1] ma zaplacic do 15 marca"              |
      |                                            |
      +---------------------+----------------------+
                            v
                           [6]
                            v
              "Jan Kowalski ma zaplacic do 15 marca"
```

Model nigdy nie widzi nazwiska. Odpowiada o `[OSOBA_1]`, a program w ostatnim
kroku podmienia etykiete z powrotem na "Jan Kowalski" — korzystajac z pliku
z kluczem, ktory przez caly czas lezal na Twoim dysku.

## Szesc warstw przetwarzania

```
   DOKUMENT --> [1] --> [2a] --+
                  |            +--> [3] --> [4] --> [5] --> dwa pliki wyzej
                  +---> [2b] --+
```

| | warstwa | co robi | wynik |
|---|---|---|---|
| 1 | **Normalizacja** | skleja to, co PDF rozerwal miedzy wiersze | tekst czytelny dla programu, oryginal nietkniety |
| 2a | **Rozpoznawanie nazw (NER)** | model jezyka wskazuje nazwiska, firmy, miejsca | lista fragmentow z ocena pewnosci |
| 2b | **Dopasowanie wzorcow** | znajduje numery o stalej budowie i sprawdza cyfre kontrolna | lista numerow bez domyslu |
| 3 | **Rozstrzyganie kolizji** | godzi oba zrodla, gdy wskazuja to samo miejsce | jedna spojna lista do wyciecia |
| 4 | **Propagacja** | to samo nazwisko znika w calym dokumencie | domkniete przypadki rozbite przez tabele |
| 5 | **Pseudonimizacja** | wstawia ponumerowane etykiety `[OSOBA_1]` | plik oczyszczony + plik z kluczem |
| 6 | **Deanonimizacja** | wstawia prawdziwe nazwy w odpowiedz modelu | tekst gotowy do uzycia |

Dwa rysunki wyzej to cala odpowiedz na pytanie, jak to dziala.
Ponizej to samo szerzej, dla ciekawych.

---

## 1. Normalizacja — porzadkowanie tekstu

Tabela w PDF-ie rozbija nazwe w polowie: "Fundacja" w jednym wierszu, "Psy Maja
Glos" w nastepnym. Numer telefonu bywa przelamany po kierunkowym. Rozerwany
kawalek nie wyglada juz jak nazwa i przeszedlby niezauwazony.

Program skleja krotkie przerwy, a dluzsze — granice kolumn w tabeli — zostawia
jako granice. Tnie zawsze oryginal, nie sklejona wersje; pamieta, ktore miejsce
odpowiada ktoremu.

## 2a. Rozpoznawanie nazw

Nazwisko nie ma stalego ksztaltu. "Kowalski", "Kowalskiego", "Kowalskiemu" to
jedno nazwisko w trzech postaciach, a listy wszystkich polskich nazwisk nie ma.
Rozpoznac je mozna tylko po tym, jak stoja w zdaniu.

Robi to model jezyka polskiego (spaCy w silniku Presidio). Bywa niepewny i myli
sie — dlatego nie jest jedynym zrodlem.

## 2b. Dopasowanie wzorcow

PESEL ma jedenascie cyfr i cyfre kontrolna. NIP ma dziesiec cyfr i wlasna
kontrole. To sa definicje z przepisow, wiec tu nie ma czego zgadywac — te dane
da sie domknac w stu procentach.

Cyfra kontrolna robi jeszcze cos wazniejszego: rozstrzyga watpliwosci. Ciag
dziesieciu cyfr moze byc NIP-em albo telefonem; NIP przechodzi swoja kontrole,
telefon nie. Dzieki temu program rozpoznaje NIP nawet wtedy, gdy nikt nie
napisal obok slowa "NIP".

Obejmuje: PESEL, NIP, REGON, KRS, numer konta, telefon, kod pocztowy, numer
dowodu, numer rejestracyjny, klucze do systemow, liste 140 polskich imion.

## 3. Rozstrzyganie kolizji

Oba zrodla czesto wskazuja to samo miejsce i przecza sobie. Numer o sprawdzonej
budowie wygrywa z domyslem modelu — dlatego NIP przestal byc oznaczany jako
telefon. Dluzszy fragment wygrywa z krotszym. Nazwy z listy wyjatkow zostaja
jawne, bo bez nich tekst traci sens i model nie zrozumie pytania.

## 4. Propagacja

Jesli nazwisko zostalo gdziekolwiek uznane za osobe, kazde jego wystapienie
w dokumencie tez znika. Tabela potrafi oddzielic "Danuty" od "Sokolowskiej";
samo nazwisko bywa dla modelu za slabym sygnalem.

To jedyne miejsce, w ktorym narzedzie jest celowo nadgorliwe. Ta reguła podniosla
wykrywanie nazwisk z 86,6 na 91,6 procent.

## 5. Pseudonimizacja

Gdyby wszyscy ludzie stali sie tym samym `[OSOBA]`, model nie odroznilby, kto
komu co zrobil — a to zwykle jest sednem pytania. Numerowanie pozwala mu sledzic,
kto jest kim, choc nie wie, jak sie nazywa.

Powstaja dwa pliki pokazane na rysunku na poczatku: oczyszczony do wyslania
i plik z kluczem, ktory czyta tylko wlasciciel konta na tym komputerze.

## 6. Deanonimizacja

Odpowiedz z `[OSOBA_1]` jest nie do czytania. Plik z kluczem wstawia prawdziwe
nazwy z powrotem. Na testach odtworzenie dalo oryginal co do znaku w 20 na 20 dokumentow.

---

## Czego to nie zalatwia

**Rozpoznanie po kontekscie.** Wyciecie nazwisk nie chroni przed ustaleniem,
o kogo chodzi. W protokole sesji rady gminy nazwa gminy padla 56 razy;
po oczyszczeniu zostala dwa razy — a jedno wystarczy, by "Wojt [OSOBA_4]"
mial tylko jedna mozliwa wartosc.

**Skany.** PDF bedacy zdjeciem strony nie ma w sobie tekstu — nie ma czego wyciac.
Program to rozpoznaje i mowi wprost, zamiast udawac, ze zadzialal.
Stary Word (.doc sprzed 2007) trzeba zapisac jako .docx.

**Cisza przy watpliwosci.** Fragmenty ponizej progu pewnosci znikaja bez zapisu
do osobnego raportu. W oknie w przegladarce widzisz jednak cala liste tego,
co znika, i podswietlony oryginal — wiec sprawdzisz to wzrokiem.

**Dane medyczne.** Rejestrow pacjentow nie anonimizuj — nie wyjmuj ich z systemu.

---

## Ile z tego dziala

Zmierzone na **324 057 slowach** polskich pism urzedowych z Biuletynow Informacji
Publicznej, w dwoch osobnych zestawach. Drugi zestaw zebralismy **po** zakonczeniu
prac, wiec narzedzie nie widzialo tych dokumentow, gdy powstawaly jego reguly.

| co | wynik |
|---|---|
| numery (PESEL, NIP, REGON, konto, telefon, kod pocztowy) | 100% |
| pelne nazwiska na dokumentach niewidzianych | 98,9% |
| odwracalnosc | 20 na 20 dokumentow |

Przez oba zestawy przeszlo jedno prawdziwe nazwisko na 287.
Sposob liczenia i pelne tabele: `pomiar/WYNIKI.md`.
