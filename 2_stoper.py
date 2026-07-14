import json
import sys
import time
import re
from core.device import TDCDevice
from core.logger import DataLogger

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def parse_raw_data(raw_string):
    pattern = r"([0-9A-Fa-f]{2})\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{12})\s+([0-9A-Fa-f]{4})"
    znalezione_pomiary = []
    
    for match in re.finditer(pattern, raw_string):
        try:
            channel = int(match.group(1), 16) 
            ts_cnt = int(match.group(3), 16)
            ts_fine = int(match.group(4), 16)
            
            parsed_value = (ts_cnt + (ts_fine / (2 ** 14))) * (1 / 0.55)
            clean_hex = match.group(0)
            
            znalezione_pomiary.append((channel, parsed_value, clean_hex))
        except ValueError:
            continue
            
    return znalezione_pomiary

def get_data_count(device):
    """Odpytuje urządzenie o ilość próbek w buforze za pomocą dataCNT."""
    resp = device.send_command("dataCNT", opoznienie=0.01)
    if resp:
        # Wyciągamy pierwszą napotkaną liczbę z odpowiedzi
        match = re.search(r'\d+', resp)
        if match:
            return int(match.group())
    return 0

def main():
    config = load_config()
    device = TDCDevice(config["serial"]["port"], config["serial"]["baudrate"], config["serial"]["timeout"])
    logger = DataLogger(config["storage"]["output_dir"])
    
    try:
        device.connect()
    except Exception as e:
        print(f"[Błąd] Brak połączenia: {e}")
        sys.exit(1)

    kanaly_z_configu = config["measurement"]["channels"]
    interwal = config["measurement"]["read_interval"]

    pliki = logger.create_new_log_files(kanaly_z_configu)

    print("=== POMIAR WIELOKANAŁOWY TIA-V110 ===")
    print(f"Monitorowane kanały zadeklarowane w JSON: {kanaly_z_configu}")
    
    limit_input = input("\nPodaj ilość próbek do pobrania (wpisz 0 dla braku limitu): ")
    try:
        limit_probek = int(limit_input)
    except ValueError:
        limit_probek = 0
        print("Nieprawidłowa wartość, ustawiono na odczyt bez limitu.")

    print("\nNaciśnij Ctrl+C, aby zatrzymać stoper.\n")
    
    try:
        # Uruchomienie pomiaru z dokładną ilością oczekiwanych próbek[cite: 2]
        device.send_command(f"measStart {limit_probek}")
        start_time = time.time()
        licznik = 0
        
        while True:
            # 1. Sprawdzenie ile próbek czeka w buforze
            ilosc_w_buforze = get_data_count(device)
            
            # 2. Pobranie danych tylko, jeśli bufor nie jest pusty
            if ilosc_w_buforze > 0:
                raw_response = device.send_command(f"dataRd {ilosc_w_buforze} hex", opoznienie=0.05)
                
                if raw_response:
                    pomiary = parse_raw_data(raw_response)
                    
                    for odczytany_kanal, parsed_val, czysty_hex in pomiary:
                        if odczytany_kanal in kanaly_z_configu:
                            licznik += 1
                            czas_trwania = time.time() - start_time
                            
                            # Zapis do plików TXT oraz do bufora dla API na bieżąco
                            logger.append_data(pliki, odczytany_kanal, czysty_hex, parsed_val)
                            
                            sys.stdout.write(f"\r[Czas: {czas_trwania:.1f}s] Zapisano: {licznik} | Ost. sygnał CH{odczytany_kanal}: {parsed_val:.6f}       ")
                            sys.stdout.flush()
                            
                            # Przerwanie pętli for, jeśli w trakcie parsowania osiągniemy limit
                            if limit_probek > 0 and licznik >= limit_probek:
                                break
            
            # Przerwanie pętli while po osiągnięciu limitu
            if limit_probek > 0 and licznik >= limit_probek:
                print(f"\n\n[Zakończono] Osiągnięto wskazany limit próbek: {limit_probek}.")
                break
                
            time.sleep(interwal)

    except KeyboardInterrupt:
        print("\n\n[Zatrzymano] Użytkownik wcisnął Ctrl+C.")
    finally:
        device.send_command("measStop")
        device.disconnect()
        print(f"Zapisano łącznie {licznik} pomiarów.")

if __name__ == "__main__":
    main()