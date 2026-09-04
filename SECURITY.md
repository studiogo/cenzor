# Bezpieczeństwo

## Co to narzędzie obiecuje

Dokumenty nie opuszczają Twojego komputera. Nie ma w nim wywołań do zewnętrznych
usług — model języka działa lokalnie, a serwer okna słucha wyłącznie na 127.0.0.1
i odmawia startu w innej konfiguracji.

## Czego nie obiecuje

Anonimizacja nie jest szczelna i nie może być. Wycięcie nazwisk nie chroni przed
rozpoznaniem osoby po treści dokumentu. Traktuj to jako zmniejszenie ryzyka,
nie jako gwarancję zgodności z RODO.

Plik z kluczem (`*-slownik.json`) zawiera wszystkie wycięte dane. Razem z plikiem
oczyszczonym odtwarza oryginał. Ma prawa dostępu 600, ale to Ty odpowiadasz za to,
gdzie go trzymasz.

## Zgłaszanie problemów

Błąd, przez który dane przeciekają do pliku wyjściowego, zgłoś przez zakładkę
Issues z opisem wzorca danych — **bez wklejania prawdziwych danych osobowych**.
Najlepiej dołącz przykład zbudowany z wymyślonych numerów.
