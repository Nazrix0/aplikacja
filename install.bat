@echo off
:: 0. Zabezpieczenie ścieżki roboczej
:: Gwarantuje, że skrypt wykona się w swoim folderze, nawet uruchomiony jako Administrator
cd /d "%~dp0"

echo ==========================================
echo    INSTALATOR SRODOWISKA - PROJEKT TDC
echo              (Windows)
echo ==========================================
echo.

:: 1. Sprawdzanie czy Python jest zainstalowany
echo [1/4] Sprawdzanie instalacji Pythona...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [BLAD] Python nie jest zainstalowany lub nie zostal dodany do zmiennej PATH!
    echo.
    echo ROZWIAZANIE: Pobierz Pythona z python.org, uruchom instalator i koniecznie
    echo zaznacz opcje "Add Python to PATH" na dole pierwszego okna przed kliknieciem Install.
    pause
    exit /b 1
)

:: 2. Tworzenie wirtualnego srodowiska
echo [2/4] Tworzenie wirtualnego srodowiska (venv)...
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [BLAD] Nie udalo sie utworzyc srodowiska wirtualnego. Sprawdz uprawnienia do folderu.
        pause
        exit /b 1
    )
    echo Venv utworzone pomyslnie.
) else (
    echo Venv i pliki aktywacyjne juz istnieja, pomijam ten krok.
)

:: 3. Aktywacja i aktualizacja narzedzia instalacyjnego
echo [3/4] Aktywacja srodowiska i aktualizacja PIP...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [BLAD] Nie udalo sie aktywowac srodowiska venv.
    pause
    exit /b 1
)
python -m pip install --upgrade pip >nul 2>&1

:: 4. Instalacja bibliotek z requirements.txt
echo [4/4] Instalacja wymaganych bibliotek...
if not exist requirements.txt (
    echo.
    echo [OSTRZEZENIE] Brak pliku requirements.txt w glownym folderze! Pakiety nie zostaly zainstalowane.
    pause
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [BLAD] Pobieranie pakietow zakonczylo sie bledem. Sprawdz polaczenie z internetem.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    INSTALACJA ZAKONCZONA SUKCESEM!
echo ==========================================
echo.
echo Aby zaczac prace, wejdz do tego folderu w terminalu (cmd/powershell) i wpisz:
echo venv\Scripts\activate
echo python 2_stoper.py
echo.
pause