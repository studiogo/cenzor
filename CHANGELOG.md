# Historia zmian

## Niewydane

- Instalator dla Windowsa: `instaluj.ps1`. Sam znajduje Pythona 3.10+, stawia
  środowisko, instaluje biblioteki i pobiera model języka
- Osobne polecenia dla Windowsa w README i na stronie projektu (`venv\Scripts\python`)
- Słownik podmian na Windowsie dostępny tylko dla zalogowanego użytkownika, tak jak
  prawa 600 na Macu i Linuksie
- Wyjście programu zawsze w UTF-8, także przekierowane do pliku na Windowsie —
  polskie litery w nazwisku albo w ścieżce nie wywracają już programu
- Skrypty pomiaru znajdują Pythona ze środowiska także na Windowsie
- Testy na GitHubie uruchamiają się też na Windowsie: instalatorem, a potem próbą
  wycięcia i odwrócenia na przykładzie

## 0.1.0 — 4 września 2026

Pierwsze wydanie.

- Rozpoznawanie polskich identyfikatorów po budowie i cyfrze kontrolnej:
  PESEL, NIP, REGON, KRS, konto, telefon, kod pocztowy, dowód, numer rejestracyjny
- Rozpoznawanie nazwisk, firm i miejscowości modelem języka polskiego
- Odwracalne podmiany: numerowane etykiety plus plik z kluczem
- Czytanie PDF, DOCX, ODT i zwykłego tekstu, rozpoznawanie formatu po zawartości
- Okno w przeglądarce z podglądem przed i po, słuchające tylko lokalnie
- Zestaw pomiarowy: dwa poligony, 324 057 słów, dwie niezależne miary
