# Anonimizuj

Wycina dane osobowe z dokumentu, zanim wyślesz go do ChatGPT, Claude albo innego
modelu. Działa w całości na Twoim komputerze — żaden plik nie wychodzi do sieci.

Po powrocie odpowiedzi wstawia prawdziwe nazwiska z powrotem, więc pracujesz
normalnie, a model nigdy nie widzi danych Twoich klientów.

```
"Umowa z Janem Kowalskim, PESEL 85010112345"
        ↓
"Umowa z [OSOBA_1], PESEL [PESEL_1]"     ← to wysyłasz do modelu
[OSOBA_1] = Jan Kowalski                  ← to zostaje na Twoim dysku
        ↓
"Jan Kowalski ma zapłacić do 15 marca"    ← odpowiedź po podmianie z powrotem
```

## Dla kogo

Dla każdego, kto ma w dokumentach cudze dane i chce korzystać z AI, nie łamiąc RODO:
księgowość, kancelarie, dział kadr, biura rachunkowe, agencje. Nie musisz umieć
programować — jest okno w przeglądarce, do którego przeciągasz plik myszką.

## Instalacja

Potrzebujesz Pythona 3.10 lub nowszego. Reszta instaluje się sama.

```bash
git clone https://github.com/studiogo/anonimizuj-pl.git
cd anonimizuj-pl
./instaluj.sh
```

Ostatni krok pobiera model języka polskiego (574 MB), więc chwilę to trwa.

## Pierwsze uruchomienie

Okno w przeglądarce — przeciągasz plik, widzisz, co zniknie, pobierasz wynik:

```bash
venv/bin/python okno/serwer.py
```

Otworzy się `http://127.0.0.1:8765`. Serwer słucha wyłącznie na Twoim komputerze
i nie da się go wystawić na sieć — to nie niedoróbka, tylko sedno narzędzia.

Wiersz poleceń, jeśli wolisz:

```bash
venv/bin/python bin/anonimizuj.py umowa.pdf --jezyk pl --podglad   # co zniknie
venv/bin/python bin/anonimizuj.py umowa.pdf --jezyk pl             # wytnij
venv/bin/python bin/odwroc.py odpowiedz.txt umowa-anon-slownik.json
```

## Co rozpoznaje

PESEL, NIP, REGON, KRS, numer konta, telefon, kod pocztowy, numer dowodu,
numer rejestracyjny, adres e-mail, klucze do systemów — po budowie i cyfrze
kontrolnej, więc bez zgadywania.

Nazwiska, nazwy firm, instytucji i miejscowości — modelem języka polskiego,
który rozpoznaje je po tym, jak stoją w zdaniu, także w odmianie.

Przyjmuje PDF, Word (.docx), OpenDocument (.odt) i zwykły tekst. Format rozpoznaje
po zawartości, nie po rozszerzeniu.

## Ile z tego działa

Zmierzone na **324 057 słowach** polskich pism urzędowych z Biuletynów Informacji
Publicznej, w dwóch osobnych zestawach. Drugi zestaw zebraliśmy **po** zakończeniu
prac, więc narzędzie nie widziało tych dokumentów, gdy powstawały jego reguły.

| co | wynik |
|---|---|
| PESEL, NIP, REGON, konto, telefon, kod pocztowy | 100% |
| pełne nazwiska na dokumentach niewidzianych | 98,9% |
| odwracalność (tekst odtworzony co do znaku) | 20 na 20 dokumentów |

Przez oba zestawy przeszło jedno prawdziwe nazwisko na 287.

Liczymy pełne nazwiska, czyli „imię plus nazwisko". Jest jeszcze miara szersza —
wszystko, co model języka uzna za osobę — i tam wychodzi 91,6% oraz 84,2%.
Ta miara bierze za osobę także nazwy ulic („Krasińskiego"), przymiotniki od
powiatów („Pułtuskiego") i wyrazy urwane przez łamanie wierszy w PDF
(„Departamen"). To nie są dane osobowe, więc im więcej takiego szumu
w dokumencie, tym niżej ta liczba spada — i tym mniej mówi.

Pomiar możesz powtórzyć u siebie — [pomiar/WYNIKI.md](pomiar/WYNIKI.md) opisuje
sposób liczenia, a `pomiar/pobierz.py` ściąga te same dokumenty z BIP-ów.
Dokumentów nie ma w repozytorium: są w nich nazwiska prawdziwych ludzi.

## Czego to nie załatwia

**Nie chroni przed rozpoznaniem po treści.** Wycięcie nazwisk nie znaczy, że nikt
nie ustali, o kogo chodzi. W protokole sesji rady gminy nazwa gminy padła 56 razy;
po oczyszczeniu została dwa razy — a jedno wystarczy, żeby „Wójt [OSOBA_4]" miał
tylko jedną możliwą wartość. Sprawdzaj wynik przed wysłaniem.

**Skany są bezużyteczne.** PDF będący zdjęciem strony nie ma w sobie tekstu.
Program powie to wprost, zamiast udawać, że zadziałał.

**Danych pacjentów nie anonimizuj.** Rejestrów medycznych po prostu nie wyjmuj
z systemu klienta.

**Plik z kluczem to cały oryginał.** Razem z plikiem oczyszczonym odtwarza
dokument w całości. Trzymaj go tam, gdzie trzymasz sam dokument, i nie wysyłaj nigdzie.

## Jak to działa w środku

Sześć warstw, dwa niezależne wykrywacze i bramka, która rozstrzyga ich spory:
[JAK-TO-DZIALA.md](JAK-TO-DZIALA.md).

## Użycie z Claude Code

Repozytorium jest jednocześnie wtyczką. Skopiuj katalog do `~/.claude/skills/`
i powiedz agentowi „zanonimizuj ten plik".

## Licencja

MIT — rób z tym, co chcesz.
