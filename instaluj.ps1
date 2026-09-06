# Stawia wszystko, czego narzedzie potrzebuje na Windowsie. Uruchom raz, po pobraniu repozytorium.
#
# Otworz PowerShell w katalogu cenzor i wpisz:
#     powershell -ExecutionPolicy Bypass -File .\instaluj.ps1
#
# "-ExecutionPolicy Bypass" jest potrzebne, bo Windows domyslnie nie uruchamia
# skryptow PowerShell pobranych z sieci. Dotyczy tylko tego jednego uruchomienia.

$ErrorActionPreference = "Stop"
$KAT = Split-Path -Parent $MyInvocation.MyCommand.Path


function Znajdz-Pythona {
    # Kolejnosc: uruchamiacz "py" (instaluje go python.org), potem "python", potem "python3".
    # Wersje sprawdzamy przez samego Pythona, bo Windows podstawia pod "python"
    # skrot do Sklepu, ktory Pythonem nie jest.
    $kandydaci = @(
        @{ Polecenie = "py";      Argumenty = @("-3") },
        @{ Polecenie = "python";  Argumenty = @() },
        @{ Polecenie = "python3"; Argumenty = @() }
    )
    foreach ($k in $kandydaci) {
        if (-not (Get-Command $k.Polecenie -ErrorAction SilentlyContinue)) { continue }
        $wersja = $null
        $poprzednie = $ErrorActionPreference
        $ErrorActionPreference = "SilentlyContinue"
        try {
            $wersja = & $k.Polecenie @($k.Argumenty) -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        } catch {
            $wersja = $null
        }
        $ErrorActionPreference = $poprzednie
        if ($LASTEXITCODE -ne 0 -or -not $wersja) { continue }
        $czesci = "$wersja".Trim().Split(".")
        if ($czesci.Length -lt 2) { continue }
        $duza = [int]$czesci[0]
        $mala = [int]$czesci[1]
        if ($duza -eq 3 -and $mala -ge 10) {
            return @{ Polecenie = $k.Polecenie; Argumenty = $k.Argumenty; Wersja = "$duza.$mala" }
        }
    }
    return $null
}


function Sprawdz-Krok($opis) {
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Nie udalo sie: $opis (kod $LASTEXITCODE). Przeczytaj komunikat wyzej i uruchom skrypt jeszcze raz."
        exit $LASTEXITCODE
    }
}


$py = Znajdz-Pythona
if ($null -eq $py) {
    Write-Host "Nie znalazlem Pythona 3.10 lub nowszego."
    Write-Host "Pobierz go z https://www.python.org/downloads/ i przy instalacji zaznacz"
    Write-Host "'Add python.exe to PATH'. Potem uruchom ten skrypt jeszcze raz."
    exit 1
}

Write-Host "1/3  Tworze srodowisko (Python $($py.Wersja))..."
$VENV = Join-Path $KAT "venv"
& $py.Polecenie @($py.Argumenty) -m venv $VENV
Sprawdz-Krok "tworzenie srodowiska"

$PYTHON = Join-Path $VENV "Scripts\python.exe"

Write-Host "2/3  Instaluje biblioteki..."
& $PYTHON -m pip install -q --upgrade pip
Sprawdz-Krok "aktualizacja pip"
& $PYTHON -m pip install -q -r (Join-Path $KAT "requirements.txt")
Sprawdz-Krok "instalacja bibliotek"

Write-Host "3/3  Pobieram model jezyka polskiego (574 MB, chwile to potrwa)..."
& $PYTHON -m spacy download pl_core_news_lg
Sprawdz-Krok "pobieranie modelu jezyka"

Write-Host ""
Write-Host "Gotowe. Sprobuj (z katalogu $KAT):"
Write-Host "  venv\Scripts\python bin\anonimizuj.py pomiar\przyklady\01-wniosek-urzedowy.txt --jezyk pl --podglad"
