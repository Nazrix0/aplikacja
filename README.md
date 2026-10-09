# ⏱️ Projekt TDC - Hybrydowy System Pomiarowy

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-lightgrey?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)

Zaawansowana aplikacja służąca jako pomost między fizycznym urządzeniem pomiarowym (Time-to-Digital Converter, np. **TIA-V110**) a zdalną aplikacją webową. 

System działa jako **hybrydowy lokalny agent**:
- 🔌 Steruje sprzętem za pomocą interfejsu szeregowego.
- 💾 Zapisuje dane offline z wykorzystaniem najwyższej precyzji matematycznej (typ `Decimal`).
- 🌐 Udostępnia lokalne API (Flask) do komunikacji z zewnętrznym serwerem przez bezpieczny tunel VPN.

---

## 🛠️ Instalacja

Projekt wykorzystuje wirtualne środowisko Python (`venv`), aby zachować izolację od systemowych bibliotek.

### 🪟 System Windows
1. Upewnij się, że masz zainstalowanego Pythona 3 z dodaną zmienną `PATH`.
2. Kliknij dwukrotnie plik `install.bat` lub uruchom go z terminala.
3. Skrypt automatycznie utworzy środowisko i zainstaluje potrzebne pakiety z `requirements.txt`.

### 🐧 System Linux (Ubuntu / Debian)
1. Otwórz terminal w głównym katalogu projektu.
2. Nadaj uprawnienia do wykonania skryptu instalacyjnego:
   ```bash
   chmod +x install.sh
   ```
3. Uruchom skrypt:
   ```bash
   ./install.sh
   ```

> ⚠️ **WAŻNE (Linux):** Skrypt może poprosić o uprawnienia `sudo`, aby doinstalować pakiet `python3-venv` oraz dodać bieżącego użytkownika do grupy `dialout` (niezbędne do komunikacji przez port szeregowy). **Po pierwszej instalacji uruchom ponownie komputer**, aby uprawnienia sprzętowe zaczęły działać!

---

## 🚀 Instrukcja Obsługi

Zanim zaczniesz pracę, **zawsze aktywuj środowisko wirtualne**:
- **Windows:** `venv\Scripts\activate`
- **Linux:** `source venv/bin/activate`

### Krok 1: Konfiguracja Peryferiów ⚙️
Uruchom kreator konfiguracji, aby dopasować ustawienia sprzętowe i pomiarowe:

```bash
python 4_edycja_peryfari.py
```

> **Uwaga na porty:** 
> - **Windows:** zazwyczaj `COM3`, `COM11` itp.
> - **Linux:** najczęściej `/dev/ttyUSB0` lub `/dev/ttyACM0`.
> 
> *Wskazówka: Jeśli nie chcesz zmieniać danej opcji w kreatorze, po prostu wciśnij klawisz `ENTER`.*

### Krok 2: Uruchomienie Pomiaru (Stoper) ⏱️
Uruchamia główną pętlę komunikującą się ze sprzętem. Loguje dane strumieniowo do plików TXT, bazy SQLite oraz bufora pamięci RAM (dla lokalnego API).

```bash
python 2_stoper.py
```

**Działanie programu:**
1. Po uruchomieniu, program nawiąże połączenie ze skonfigurowanym portem i zapyta o pożądaną liczbę próbek.
2. Wpisz `0`, aby mierzyć w nieskończoność (aż do ręcznego zatrzymania).
3. Pomiary zapisywane są w czasie rzeczywistym (na ekranie widać licznik zapisanych próbek oraz bieżący czas).
4. Aby bezpiecznie zatrzymać stoper i zamknąć połączenie, wciśnij skrót **`Ctrl+C`**.

### Krok 3: Analiza i Wykresy (wyniki.py) 📊
Skrypt analityczny automatycznie wykrywa uszkodzone wartości, inteligentnie formatuje oś czasu i generuje interaktywne wykresy Matplotlib. Posiada dwa tryby działania:

#### Tryb A: Analiza z plików tekstowych
Wymaga podania ścieżek do dwóch konkretnych plików z zapisanymi pomiarami.
```bash
python wyniki.py -p1 wyniki_pomiarow/pomiar_przeliczone_A.txt -p2 wyniki_pomiarow/pomiar_przeliczone_B.txt
```

#### Tryb B: Analiza bezpośrednio z bazy SQLite
Automatycznie pobiera i zestawia ze sobą chronologiczne pomiary z wybranych kanałów wejściowych.
```bash
python wyniki.py -c1 1 -c2 2 -l 500
```
*(Powyższa komenda pobierze z bazy danych maksymalnie 500 ostatnich pomiarów dla kanału 1 oraz 2 i wygeneruje ich porównanie).*

**Dostępne parametry CLI:**
| Parametr | Opis |
| --- | --- |
| `-p1`, `-p2` | Ścieżki do plików wejściowych (wymagane w Trybie A). |
| `-c1`, `-c2` | Numery kanałów do porównania z bazy danych (wymagane w Trybie B). |
| `-db` | *(Opcjonalnie)* Ścieżka do bazy. Domyślnie: `wyniki_pomiarow/baza_lokalna.db`. |
| `-l`, `--limit`| Maksymalna liczba wczytywanych próbek (wartość `0` = wszystkie dane). |

### Krok 4: Uruchomienie lokalnego API 🌐
Aby udostępnić bieżące odczyty ze stopera do zewnętrznego serwera przez dedykowaną sieć VPN, uruchom lokalną aplikację webową (Flask):

```bash
python 3_uruchom_api.py
```

---

## 📂 Struktura Projektu

```text
.
├── api/                        # Aplikacja Flask udostępniająca lokalne endpointy
├── core/                       
│   ├── device.py               # Niskopoziomowa, bezpieczna obsługa portu szeregowego
│   ├── logger.py               # System logowania (TXT, SQLite, RAM bufor)
│   └── stoper.py               # Parser Hex z precyzją zmiennoprzecinkową (Decimal)
├── 2_stoper.py                 # Główny skrypt pomiarowy CLI
├── 3_uruchom_api.py            # Skrypt startowy serwera API
├── 4_edycja_peryfari.py        # Interaktywny konfigurator sprzętowy
├── config.json                 # Plik przechowujący parametry konfiguracyjne
└── wyniki.py                   # Interfejs analityczno-wizualny Matplotlib (CLI)
```