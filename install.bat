@echo off
echo ==========================================
echo    INSTALATOR SRODOWISKA - PROJEKT TDC
echo ==========================================
echo.

:: 1. Sprawdzanie czy Python jest zainstalowany
echo [1/4] Sprawdzanie instalacji Pythona...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [BLAD] Python nie jest zainstalowany lub nie zostal dodany do zmiennej PATH!
    echo Zainstaluj Pythona z oficjalnej strony i zaznacz opcje "Add Python to PATH".
    pause
    exit /b
)

:: 2. Tworzenie wirtualnego środowiska
echo [2/4] Tworzenie wirtualnego srodowiska (venv)...
if not exist venv (
    python -m venv venv
    echo Venv utworzone pomyslnie.
) else (
    echo Venv juz istnieje, pomijam ten krok.
)

:: 3. Aktywacja i aktualizacja narzędzia instalacyjnego
echo [3/4] Aktywacja srodowiska i aktualizacja PIP...
call venv\Scripts\activate
python -m pip install --upgrade pip >nul 2>&1

:: 4. Instalacja bibliotek z requirements.txt
echo [4/4] Instalacja wymaganych bibliotek...
if exist requirements.txt (
    pip install -r requirements.txt
    echo.
    echo ==========================================
    echo    INSTALACJA ZAKONCZONA SUKCESEM!
    echo ==========================================
) else (
    echo.
    echo [OSTRZEZENIE] Brak pliku requirements.txt! Pakiety nie zostaly zainstalowane.
)

echo.
echo Aby zaczac prace, po prostu wpisz w terminalu:
echo venv\Scripts\activate
echo python 2_stoper.py
echo.
pause