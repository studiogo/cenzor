---
name: anonimizuj
description: Wycina dane osobowe z tekstu, zanim pojdzie do modelu w chmurze — nazwiska, firmy, miejsca, maile, telefony i klucze, takze te, ktorych nie ma na zadnej liscie. Podmiany zapisuje w slowniku, wiec da sie je odwrocic po powrocie tekstu. Use when the user says "zanonimizuj", "wytnij dane osobowe", "ukryj nazwiska", "przygotuj do wyslania", "usun wrazliwe dane z pliku", albo gdy do modelu ma pojsc plik z danymi klienta.
---

# Anonimizuj

Dziala lokalnie, nic nie wychodzi na zewnatrz. Rozpoznaje dane osobowe po budowie zdania
(Presidio + spaCy), wiec lapie nazwiska i firmy, ktorych nigdy wczesniej nie widzialo.

## Okno w przegladarce

Dla kogos, kto nie pracuje w terminalu — przeciaga plik myszka i widzi,
co zniknie, zanim cokolwiek wysle:

    ~/.claude/skills/anonimizuj/venv/bin/python ~/.claude/skills/anonimizuj/okno/serwer.py

Serwer slucha wylacznie na tym komputerze (127.0.0.1). Nie da sie go wystawic na siec.

## Praca

Przyjmuje PDF, Word (.docx), OpenDocument (.odt) i zwykly tekst — format
rozpoznaje po zawartosci, nie po rozszerzeniu. Wynikiem zawsze jest tekst.

Podglad — pokazuje, co zostaloby wyciete, i niczego nie zapisuje:

    ~/.claude/skills/anonimizuj/venv/bin/python \
      ~/.claude/skills/anonimizuj/bin/anonimizuj.py plik.txt --podglad

Wyciecie — daje plik `-anon` do wyslania oraz `-slownik.json`, ktory zostaje na dysku:

    ~/.claude/skills/anonimizuj/venv/bin/python \
      ~/.claude/skills/anonimizuj/bin/anonimizuj.py plik.txt

Odwrocenie — wstawia prawdziwe nazwy do tekstu, ktory wrocil z etykietami:

    ~/.claude/skills/anonimizuj/venv/bin/python \
      ~/.claude/skills/anonimizuj/bin/odwroc.py odpowiedz.txt plik-anon-slownik.json

Tekst polski: dodaj `--jezyk pl`. Wymaga modelu `pl_core_news_lg`:

    ~/.claude/skills/anonimizuj/venv/bin/python -m spacy download pl_core_news_lg

Bez niego skrypt odmawia pracy zamiast po cichu przepuszczac nazwiska.

## Pomiar

Katalog `pomiar/` trzyma zestaw testowy i wyniki. Dokumentow w nim nie ma —
`pobierz.py` sciaga je z BIP-ow na Twoj dysk wedlug adresow z `ZRODLA.md`.

    python3 pomiar/pobierz.py poligon
    python3 pomiar/pomiar.py poligon      # miara glowna
    python3 pomiar/kontrola.py poligon    # miara niezalezna od listy imion

Ostatni wynik na 97 082 slowach polskich pism urzedowych: identyfikatory
(PESEL, NIP, REGON, konto, telefon, mail, kod pocztowy) 100%, nazwiska 91,6%
w mierze niezaleznej, odwracalnosc 10/10. Szczegoly i ograniczenia: `pomiar/WYNIKI.md`.

## Konfiguracja

Plik `konfiguracja.json` w katalogu skilla:

- `encje` — co ma znikac (PERSON, ORG, LOCATION, EMAIL_ADDRESS, PHONE_NUMBER i inne).
- `nie_ruszaj` — nazwy, ktore maja zostac jawne, bo bez nich tekst traci sens.
- `prog_pewnosci` — nizej znaczy ostrozniej, ale wiecej falszywych trafien. Domyslnie 0.4.
- `jezyk` — `en` albo `pl`.

## Czego to nie zalatwia

Nazwisko oddzielone od imienia granica komorki w tabeli potrafi przejsc —
to zrodlo wiekszosci brakujacych procent.

Anonimizacja transkrypcji nigdy nie jest szczelna. Po wycieciu nazwisk zostaje tresc,
po ktorej firme da sie rozpoznac. Chroni przed przypadkowym wyciekiem nazwiska,
nie przed rozpoznaniem klienta.

Dane pacjentow, wierszy z tabel medycznych i podobnych rejestrow nie anonimizuj —
po prostu ich nie wyjmuj z systemu klienta.

## Powiazane

Slownik podmian ma prawa 600 (tylko wlasciciel). Nie wysylaj go nigdzie razem z tekstem.
