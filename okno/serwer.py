#!/usr/bin/env python3
"""Okno w przegladarce do anonimizacji dokumentow.

Serwer sluchа WYLACZNIE na tym komputerze (127.0.0.1). Nie da sie go wystawic
na siec — to nie jest niedorobka, tylko sedno narzedzia. W chwili, w ktorej
dokumenty zaczelyby jechac przez siec na cudza maszyne, obietnica "nic nie
wychodzi z Twojego komputera" przestaje byc prawdziwa.

    python3 okno/serwer.py
"""
import base64, json, os, sys, tempfile, threading, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

KAT = Path(__file__).resolve().parent
SKILL = KAT.parent
sys.path.insert(0, str(SKILL / "bin"))

PORT = int(os.environ.get("ANONIMIZUJ_PORT", "8765"))
ADRES = "127.0.0.1"


def przetworz(nazwa, dane_b64, jezyk):
    """Zwraca podglad: oryginal, wersje oczyszczona i liste tego, co znika."""
    import anonimizuj as A
    from wczytaj import wczytaj, BladOdczytu

    surowe = base64.b64decode(dane_b64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(nazwa).suffix or ".txt") as f:
        f.write(surowe)
        tymczasowy = Path(f.name)
    try:
        tekst, format_pliku = wczytaj(tymczasowy)
    except BladOdczytu as e:
        return {"blad": str(e)}
    finally:
        tymczasowy.unlink(missing_ok=True)

    konfig = A.wczytaj_konfig()
    konfig["jezyk"] = jezyk
    trafienia = A.znajdz(tekst, konfig)
    czysty, slownik = A.podmien(tekst, trafienia)

    pozycje = {}
    for _, _, typ, fragment in trafienia:
        etykieta = A.ETYKIETY.get(typ, typ)
        klucz = (etykieta, fragment)
        pozycje[klucz] = pozycje.get(klucz, 0) + 1
    lista = [{"typ": e, "tekst": f, "ile": n}
             for (e, f), n in sorted(pozycje.items(), key=lambda x: (-x[1], x[0]))]

    return {
        "format": format_pliku,
        "slow": len(tekst.split()),
        "oryginal": tekst,
        "oczyszczony": czysty,
        "znika": lista,
        "wystapien": len(trafienia),
        "roznych": len(slownik),
        "slownik": slownik,
        "nazwa": Path(nazwa).stem,
    }


class Uchwyt(BaseHTTPRequestHandler):
    def _odpowiedz(self, kod, typ, tresc):
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(tresc)))
        self.end_headers()
        self.wfile.write(tresc)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._odpowiedz(200, "text/html; charset=utf-8",
                            (KAT / "strona.html").read_bytes())
        else:
            self._odpowiedz(404, "text/plain; charset=utf-8", b"nie ma takiej strony")

    def do_POST(self):
        if self.path != "/przetworz":
            return self._odpowiedz(404, "text/plain; charset=utf-8", b"nie ma")
        dlugosc = int(self.headers.get("Content-Length", 0))
        zadanie = json.loads(self.rfile.read(dlugosc) or b"{}")
        try:
            wynik = przetworz(zadanie.get("nazwa", "plik.txt"),
                              zadanie.get("dane", ""),
                              zadanie.get("jezyk", "pl"))
        except Exception as e:
            wynik = {"blad": f"{type(e).__name__}: {e}"}
        self._odpowiedz(200, "application/json; charset=utf-8",
                        json.dumps(wynik, ensure_ascii=False).encode("utf-8"))

    def log_message(self, *a):
        pass          # cisza w terminalu — nazwy plikow to tez dane


def main():
    # Windows zapisuje wyjscie przekierowane do pliku w cp1250 — polska litera
    # w sciezce wywraca wtedy program. Na Macu i Linuksie to nic nie zmienia.
    for strumien in (sys.stdout, sys.stderr):
        if hasattr(strumien, "reconfigure"):
            strumien.reconfigure(encoding="utf-8", errors="replace")
    try:
        serwer = HTTPServer((ADRES, PORT), Uchwyt)
    except OSError as e:
        if os.name == "nt":
            rada = (f"Zmien port. W PowerShellu:  $env:ANONIMIZUJ_PORT=8080; python {__file__}\n"
                    f"            w cmd:         set ANONIMIZUJ_PORT=8080 && python {__file__}")
        else:
            rada = f"Zmien port: ANONIMIZUJ_PORT=8080 python3 {__file__}"
        sys.exit(f"Nie moge zajac portu {PORT} na {ADRES}: {e}\n{rada}")
    adres = f"http://{ADRES}:{PORT}"
    print(f"Okno dziala pod adresem {adres}")
    print("Slucha tylko na tym komputerze. Zeby zamknac: Ctrl+C")
    threading.Timer(0.6, lambda: webbrowser.open(adres)).start()
    try:
        serwer.serve_forever()
    except KeyboardInterrupt:
        print("\nZamkniete.")


if __name__ == "__main__":
    main()
