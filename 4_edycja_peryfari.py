import json
import os

# Definiujemy ścieżkę do pliku z konfiguracją
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n[Sukces] Plik {CONFIG_FILE} został pomyślnie zaktualizowany.")

def main():
    config = load_config()
    
    if not config:
        print(f"[Błąd] Nie można odnaleźć pliku {CONFIG_FILE} w obecnym folderze.")
        return

    print("=== EDYTOR PLIKU KONFIGURACYJNEGO TDC ===")
    print("Wciśnij klawisz ENTER, aby zachować obecną wartość bez jej zmieniania.\n")
    
    # Edycja ustawień portu szeregowego
    obecny_port = config["serial"]["port"]
    nowy_port = input(f"1. Port COM (obecnie: {obecny_port}): ")
    if nowy_port.strip():
        config["serial"]["port"] = nowy_port.strip()

    # Edycja monitorowanych kanałów pomiarowych
    obecne_kanaly = config["measurement"]["channels"]
    nowe_kanaly = input(f"2. Aktywne kanały (obecnie: {obecne_kanaly}) - podaj oddzielone przecinkiem np. 1,2: ")
    if nowe_kanaly.strip():
        try:
            # Konwersja wprowadzonego tekstu z powrotem na listę liczb całkowitych
            config["measurement"]["channels"] = [int(x.strip()) for x in nowe_kanaly.split(",")]
        except ValueError:
            print("  -> Zignorowano (niepoprawny format, wpisz np. 1,2)")

    # Edycja interwału odczytu
    obecny_interwal = config["measurement"]["read_interval"]
    nowy_interwal = input(f"3. Interwał odczytu w sekundach (obecnie: {obecny_interwal}): ")
    if nowy_interwal.strip():
        try:
            config["measurement"]["read_interval"] = float(nowy_interwal.strip())
        except ValueError:
            print("  -> Zignorowano (niepoprawny format liczby)")

    # Zapis
    save_config(config)

if __name__ == "__main__":
    main()