# Współpraca

## Zanim wyślesz zmianę

Każda zmiana w wykrywaniu musi przejść pomiar. Inaczej nie wiadomo, czy poprawia,
czy cofa.

```bash
python3 pomiar/pobierz.py poligon      # ściąga dokumenty z BIP-ów na Twój dysk
python3 pomiar/pomiar.py poligon       # miara główna
python3 pomiar/kontrola.py poligon     # miara niezależna od listy imion
```

W opisie zmiany podaj obie liczby przed i po. Spadek w którejkolwiek kategorii
wymaga uzasadnienia.

## Czego nie wysyłać

Dokumentów z prawdziwymi danymi — ani do repozytorium, ani jako załącznik do
zgłoszenia. Przykłady buduj z wymyślonych numerów; `pomiar/przyklady/` pokazuje jak.

## Nowe wzorce

Identyfikator z cyfrą kontrolną dopisz razem z funkcją sprawdzającą tę cyfrę.
Wzorzec bez kontroli łapie za dużo i psuje wynik w innych kategoriach.
