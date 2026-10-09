import argparse
import os
import sys
import sqlite3
import numpy as np
import matplotlib.pyplot as plt

# Wymuszenie ładnego, nowoczesnego stylu dla wykresów
plt.style.use('ggplot')

def wczytaj_dane(nazwa_pliku):
    """Wczytuje przeliczone dane z pliku tekstowego."""
    wartosci = []
    if not os.path.exists(nazwa_pliku):
        print(f"[Błąd] Plik '{nazwa_pliku}' nie istnieje.")
        return []
        
    try:
        with open(nazwa_pliku, 'r', encoding='utf-8') as plik:
            for linia in plik:
                linia = linia.strip()
                if linia and not linia.startswith("PRZELICZONA") and not linia.startswith("-"):
                    try:
                        wartosci.append(float(linia.replace(',', '.')))
                    except ValueError:
                        continue
    except Exception as e:
        print(f"[Błąd] Nie udało się odczytać pliku '{nazwa_pliku}': {e}")
        
    return wartosci

def wczytaj_z_bazy(sciezka_db, kanal, limit=0):
    """Wczytuje chronologiczne dane z bazy SQLite dla konkretnego kanału."""
    wartosci = []
    if not os.path.exists(sciezka_db):
        print(f"[Błąd] Baza danych '{sciezka_db}' nie istnieje.")
        return []

    try:
        conn = sqlite3.connect(sciezka_db)
        cursor = conn.cursor()
        
        query = "SELECT parsed_value FROM pomiary WHERE channel = ? ORDER BY timestamp ASC, id ASC"
        if limit > 0:
            query += f" LIMIT {limit}"
            
        cursor.execute(query, (kanal,))
        wyniki = cursor.fetchall()
        
        for wiersz in wyniki:
            try:
                # Konwersja tekstu z bazy z powrotem na float dla wykresu
                wartosci.append(float(wiersz[0]))
            except (ValueError, TypeError):
                continue
                
        conn.close()
    except Exception as e:
        print(f"[Błąd bazy danych] Nie udało się pobrać danych z bazy: {e}")
        
    return wartosci

def formatuj_wykres(ax, tytul, os_y_etykieta):
    """Funkcja pomocnicza nadająca jednolity wygląd wykresom."""
    ax.set_title(tytul, fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel(os_y_etykieta, fontsize=11, fontweight='bold')
    ax.grid(True, axis='y', linestyle='--', alpha=0.7, color='gray')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def main():
    # 1. OTOCZKA (Interfejs CLI)
    parser = argparse.ArgumentParser(
        description="Narzędzie Analityczne TDC - Porównywanie i wizualizacja danych.",
        epilog="Przykład (Pliki): python wyniki.py -p1 dane_A.txt -p2 dane_B.txt\n"
               "Przykład (Baza):  python wyniki.py -db baza.db -c1 1 -c2 2 -l 500"
    )
    
    # Opcja A: Wczytywanie z plików
    grupa_pliki = parser.add_argument_group('Źródło: Pliki Tekstowe')
    grupa_pliki.add_argument('-p1', '--plik1', help="Ścieżka do pierwszego pliku")
    grupa_pliki.add_argument('-p2', '--plik2', help="Ścieżka do drugiego pliku")
    
    # Opcja B: Wczytywanie z bazy danych
    grupa_baza = parser.add_argument_group('Źródło: Baza Danych (SQLite)')
    grupa_baza.add_argument('-db', '--baza', default="wyniki_pomiarow/baza_lokalna.db", help="Ścieżka do bazy (domyślnie: wyniki_pomiarow/baza_lokalna.db)")
    grupa_baza.add_argument('-c1', '--kanal1', type=int, help="Numer kanału A do pobrania z bazy")
    grupa_baza.add_argument('-c2', '--kanal2', type=int, help="Numer kanału B do pobrania z bazy")
    grupa_baza.add_argument('-l', '--limit', type=int, default=0, help="Maksymalna ilość próbek do pobrania (0 = bez limitu)")
    
    args = parser.parse_args()

    print("=================================================")
    print("      ANALIZATOR WYNIKÓW TDC (Wizualizacja)      ")
    print("=================================================")

    dane1, dane2 = [], []
    etykieta1, etykieta2 = "", ""

    # 2. LOGIKA WYBORU ŹRÓDŁA DANYCH
    if args.plik1 and args.plik2:
        print(f"[*] Tryb odczytu: PLIKI TEKSTOWE")
        print(f" -> Plik 1: {args.plik1}")
        print(f" -> Plik 2: {args.plik2}")
        dane1 = wczytaj_dane(args.plik1)
        dane2 = wczytaj_dane(args.plik2)
        etykieta1 = f"Plik ({os.path.basename(args.plik1)})"
        etykieta2 = f"Plik ({os.path.basename(args.plik2)})"

    elif args.kanal1 is not None and args.kanal2 is not None:
        print(f"[*] Tryb odczytu: BAZA DANYCH SQLITE")
        print(f" -> Baza: {args.baza}")
        print(f" -> Pobieranie: Kanał {args.kanal1} vs Kanał {args.kanal2} (Limit: {'Brak' if args.limit == 0 else args.limit})")
        dane1 = wczytaj_z_bazy(args.baza, args.kanal1, args.limit)
        dane2 = wczytaj_z_bazy(args.baza, args.kanal2, args.limit)
        etykieta1 = f"Baza (Kanał {args.kanal1})"
        etykieta2 = f"Baza (Kanał {args.kanal2})"
        
    else:
        print("[Błąd] Użycie skryptu jest niepełne.")
        print("Musisz podać ALBO dwa pliki (-p1 oraz -p2), ALBO dwa kanały z bazy (-c1 oraz -c2).")
        print("Użyj 'python wyniki.py -h' aby zobaczyć pomoc.")
        sys.exit(1)

    # 3. WALIDACJA DANYCH
    print(f"\n[Status] Wczytano danych:\n -> Zestaw A: {len(dane1)} próbek\n -> Zestaw B: {len(dane2)} próbek")
    if not dane1 and not dane2:
        print("\n[Ostrzeżenie] Oba źródła są puste. Wykres nie zostanie wygenerowany.")
        sys.exit(1)

    # Wyrównanie danych (wypełnienie zerami)
    liczba_wierszy = max(len(dane1), len(dane2))
    dane1.extend([0.0] * (liczba_wierszy - len(dane1)))
    dane2.extend([0.0] * (liczba_wierszy - len(dane2)))

    # Obliczenia analityczne
    roznice = [w1 - w2 for w1, w2 in zip(dane1, dane2)]
    mnoznik = 1_000_000_000
    dane1_skorygowane = [w - (i * mnoznik) for i, w in enumerate(dane1, start=1)]
    dane2_skorygowane = [w - (i * mnoznik) for i, w in enumerate(dane2, start=1)]

    # Konfiguracja osi X
    os_x = np.arange(1, liczba_wierszy + 1)
    szerokosc = 0.35

    print("\n[Trwa Generowanie Wykresów...]")
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 14), sharex=True)
    fig.canvas.manager.set_window_title('Analiza Danych TDC')

    kolor_p1 = '#1f77b4'
    kolor_p2 = '#ff7f0e'
    kolor_p1_korekta = '#673AB7'
    kolor_p2_korekta = '#00BCD4'

    # WYKRES 1: WARTOŚCI SUROWE
    ax1.bar(os_x - szerokosc/2, dane1, szerokosc, label=etykieta1, color=kolor_p1, edgecolor='black', linewidth=0.5)
    ax1.bar(os_x + szerokosc/2, dane2, szerokosc, label=etykieta2, color=kolor_p2, edgecolor='black', linewidth=0.5)
    formatuj_wykres(ax1, '1. Zestawienie Wartości Oryginalnych', 'Wartość Czasu [s]')
    ax1.legend(loc='upper left', frameon=True, shadow=True)

    # WYKRES 2: RÓŻNICE
    kolory_roznicy = ['#2ca02c' if r >= 0 else '#d62728' for r in roznice]
    slupki = ax2.bar(os_x, roznice, szerokosc * 1.5, color=kolory_roznicy, edgecolor='black', linewidth=0.5)
    formatuj_wykres(ax2, '2. Różnica Absolutna (Zestaw A - Zestaw B)', 'Różnica')
    ax2.axhline(0, color='black', linewidth=1.2)
    
    if liczba_wierszy <= 30:
        ax2.bar_label(slupki, fmt='%.2f', padding=5, fontsize=9, rotation=45)

    # WYKRES 3: ODJĘCIE TRENDU
    ax3.bar(os_x - szerokosc/2, dane1_skorygowane, szerokosc, label='A (Skorygowane)', color=kolor_p1_korekta, edgecolor='black', linewidth=0.5)
    ax3.bar(os_x + szerokosc/2, dane2_skorygowane, szerokosc, label='B (Skorygowane)', color=kolor_p2_korekta, edgecolor='black', linewidth=0.5)
    formatuj_wykres(ax3, f'3. Wartości po Detrendingu (- Numer próbki × {mnoznik})', 'Odchylenie')
    ax3.axhline(0, color='black', linewidth=1.2)
    ax3.legend(loc='upper left', frameon=True, shadow=True)
    ax3.set_xlabel('Numer Próbki (Oś Czasu)', fontsize=12, fontweight='bold')

    # DYNAMICZNA OŚ X
    ax3.set_xticks(os_x)
    if liczba_wierszy <= 40:
        ax3.set_xticklabels(os_x, rotation=0, fontsize=10)
    elif liczba_wierszy <= 100:
        ax3.set_xticklabels(os_x, rotation=90, fontsize=8)
    else:
        ax3.xaxis.set_major_locator(plt.MaxNLocator(integer=True, nbins=30))
        ax3.tick_params(axis='x', rotation=45)

    plt.tight_layout(pad=3.0)
    plt.show()

if __name__ == "__main__":
    main()