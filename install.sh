#!/bin/bash

echo "=========================================="
echo "   INSTALATOR ŚRODOWISKA - PROJEKT TDC"
echo "=========================================="
echo ""

# 1. Sprawdzanie czy Python jest zainstalowany
echo "[1/4] Sprawdzanie instalacji Pythona..."
if ! command -v python3 &> /dev/null; then
    echo "[BŁĄD] Python3 nie jest zainstalowany!"
    exit 1
fi

# 2. Tworzenie wirtualnego środowiska
echo "[2/4] Tworzenie wirtualnego środowiska (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Venv utworzone pomyślnie."
else
    echo "Venv już istnieje, pomijam ten krok."
fi

# 3. Aktywacja i aktualizacja narzędzia instalacyjnego
echo "[3/4] Aktywacja środowiska i aktualizacja PIP..."
source venv/bin/activate
python3 -m pip install --upgrade pip &> /dev/null

# 4. Instalacja bibliotek
echo "[4/4] Instalacja wymaganych bibliotek..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo ""
    echo "=========================================="
    echo "   INSTALACJA ZAKOŃCZONA SUKCESEM!"
    echo "=========================================="
else
    echo ""
    echo "[OSTRZEŻENIE] Brak pliku requirements.txt! Pakiety nie zostały zainstalowane."
fi

echo ""
echo "Aby zacząć pracę, wpisz w terminalu:"
echo "source venv/bin/activate"
echo "python3 2_stoper.py"
echo ""