import json
import os
import sys

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[Błąd] Nie można odnaleźć pliku {CONFIG_FILE}.")
        sys.exit(1)
    try:
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[Błąd] Plik {CONFIG_FILE} jest uszkodzony: {e}")
        sys.exit(1)

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"\n[Sukces] Plik {CONFIG_FILE} został pomyślnie zaktualizowany!")
    except Exception as e:
        print(f"\n[Błąd zapisu] Nie udało się zapisać zmian: {e}")

def pobierz_wartosc(komunikat, obecna_wartosc, typ_danych=str):
    """Pomocnicza funkcja do bezpiecznego pobierania i formatowania wejścia."""
    while True:
        wejscie = input(f"{komunikat} (obecnie: {obecna_wartosc}): ").strip()
        
        if not wejscie:
            return obecna_wartosc # Użytkownik wcisnął ENTER (zachowaj starą)
            
        try:
            # Konwersja na oczekiwany typ
            if typ_danych == list:
                return [int(x.strip()) for x in wejscie.split(",")]
            else:
                return typ_danych(wejscie)
        except ValueError:
            print(f"  -> [Błąd] Niepoprawny format. Oczekiwany typ to: {typ_danych.__name__}. Spróbuj ponownie.")

def main():
    config = load_config()

    print("=================================================")
    print("      EDYTOR KONFIGURACJI SPRZĘTOWEJ TDC         ")
    print("=================================================")
    print("Wskazówka: Wciśnij ENTER, aby zostawić obecną wartość.\n")
    
    # 1. Sekcja Serial
    print("--- 1. Ustawienia Portu Szeregowego ---")
    config["serial"]["port"] = pobierz_wartosc("Port COM/USB", config["serial"]["port"], str)
    config["serial"]["baudrate"] = pobierz_wartosc("Prędkość transmisji (Baudrate)", config["serial"]["baudrate"], int)
    config["serial"]["timeout"] = pobierz_wartosc("Limit czasu odpowiedzi [s]", config["serial"]["timeout"], float)

    print("\n--- 2. Ustawienia Pomiarowe ---")
    # Konwersja listy na string dla ładniejszego wyświetlania
    obecne_kanaly_str = ",".join(map(str, config["measurement"]["channels"]))
    nowe_kanaly = pobierz_wartosc("Aktywne kanały (np. 1,2)", obecne_kanaly_str, list)
    config["measurement"]["channels"] = nowe_kanaly
    
    config["measurement"]["threshold"] = pobierz_wartosc("Próg napięcia (Threshold) [V]", config["measurement"]["threshold"], float)
    config["measurement"]["edge"] = pobierz_wartosc("Zbocze (r - rosnące, f - opadające)", config["measurement"]["edge"], str)
    config["measurement"]["read_interval"] = pobierz_wartosc("Interwał odczytu pętli [s]", config["measurement"]["read_interval"], float)

    # Zapis
    save_config(config)

if __name__ == "__main__":
    main()