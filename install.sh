#!/bin/bash

echo "=========================================="
echo "   INSTALATOR ŚRODOWISKA - PROJEKT TDC"
echo "         (Ubuntu / Debian)"
echo "=========================================="
echo ""

# Zatrzymanie skryptu w przypadku krytycznego błędu
set -e

# 1. Sprawdzenie i instalacja pakietów systemowych
echo "[1/5] Sprawdzanie pakietów systemowych (Python3, venv)..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 nie jest zainstalowany. Próbuję zainstalować..."
    sudo apt-get update
    sudo apt-get install -y python3
fi

# Ubuntu i Debian wymagają osobnego pakietu do obsługi venv
if ! dpkg -l | grep -q python3-venv; then
    echo "Pakiet python3-venv nie jest zainstalowany. Próbuję zainstalować..."
    sudo apt-get update
    sudo apt-get install -y python3-venv
fi

# 2. Uprawnienia do komunikacji sprzętowej
echo "[2/5] Konfiguracja uprawnień do portu szeregowego (dialout)..."
if ! groups $USER | grep -q "\bdialout\b"; then
    echo "Dodawanie użytkownika $USER do grupy dialout (wymagane sudo)..."
    sudo usermod -aG dialout $USER
    echo "-> UWAGA: Aby uprawnienia sprzętowe zadziałały, po instalacji konieczne będzie ponowne zalogowanie do systemu lub restart komputera!"
else
    echo "Użytkownik $USER ma już odpowiednie uprawnienia sprzętowe."
fi

# 3. Tworzenie wirtualnego środowiska
echo "[3/5] Tworzenie wirtualnego środowiska (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Venv utworzone pomyślnie."
else
    echo "Venv już istnieje, pomijam ten krok."
fi

# 4. Aktywacja i aktualizacja narzędzia instalacyjnego
echo "[4/5] Aktywacja środowiska i aktualizacja PIP..."
source venv/bin/activate
python3 -m pip install --upgrade pip > /dev/null

# 5. Instalacja bibliotek z requirements.txt
echo "[5/5] Instalacja wymaganych bibliotek..."
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
echo "Aby zacząć pracę z aplikacją, wpisz w terminalu:"
echo "source venv/bin/activate"
echo "python3 2_stoper.py"
echo ""