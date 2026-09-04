#!/usr/bin/env bash
# Stawia wszystko, czego narzedzie potrzebuje. Uruchom raz, po pobraniu repozytorium.
set -e
KAT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "1/3  Tworze srodowisko..."
python3 -m venv "$KAT/venv"
echo "2/3  Instaluje biblioteki..."
"$KAT/venv/bin/pip" install -q --upgrade pip
"$KAT/venv/bin/pip" install -q -r "$KAT/requirements.txt"
echo "3/3  Pobieram model jezyka polskiego (574 MB, chwile to potrwa)..."
"$KAT/venv/bin/python" -m spacy download pl_core_news_lg
echo
echo "Gotowe. Sprobuj:"
echo "  $KAT/venv/bin/python $KAT/bin/anonimizuj.py $KAT/pomiar/przyklady/01-wniosek-urzedowy.txt --jezyk pl --podglad"
