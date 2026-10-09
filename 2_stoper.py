import json
import sys
import time
import re
import logging
from decimal import Decimal, getcontext, InvalidOperation
from core.device import TDCDevice
from core.logger import DataLogger

# Zabezpieczenie przed gubieniem precyzji w długich cyklach czasu
getcontext().prec = 35
logging.basicConfig(level=logging.INFO, format='%(message)s')

def load_config(path="config.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"[Błąd] Brak pliku {path}. Uruchom skrypt konfiguracyjny.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"[Błąd] Plik {path} jest uszkodzony: {e}")
        sys.exit(1)

def parse_raw_data(raw_string):
    if not raw_string:
        return []
        
    pattern = r"([0-9A-Fa-f]{2})\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{12})\s+([0-9A-Fa-f]{4})"
    znalezione_pomiary = []
    
    # Przeliczniki konwertowane raz jako obiekty Decimal
    mnoznik = Decimal('1') / Decimal('0.55')
    dzielnik = Decimal(2 ** 14)
    
    for match in re.finditer(pattern, raw_string):
        try:
            channel = int(match.group(1), 16) 
            ts_cnt = Decimal(int(match.group(3), 16))
            ts_fine = Decimal(int(match.group(4), 16))
            
            # Bezpieczne matematycznie zliczanie unikające błędu standardu IEEE 754 float
            parsed_value = (ts_cnt + (ts_fine / dzielnik)) * mnoznik
            clean_hex = match.group(0)
            
            znalezione_pomiary.append((channel, parsed_value, clean_hex))
        except (ValueError, TypeError, InvalidOperation):
            # Zignorowanie ewentualnych śmieci w transmisji po kablu i kontynuowanie pracy
            continue
            
    return znalezione_pomiary

def get_data_count(device):
    """Odpytuje urządzenie o ilość próbek w buforze za pomocą dataCNT."""
    try:
        resp = device.send_command("dataCNT", opoznienie=0.01)
        if resp:
            # Wyciągamy pierwszą napotkaną liczbę z odpowiedzi
            match = re.search(r'\d+', resp)
            if match:
                return int(match.group())
    except Exception as e:
        logging.debug(f"[Stoper] Błąd odpytywania bufora: {e}")
    return 0

def main():
    config = load_config()
    
    # Walidacja poprawności kluczy struktury JSON
    try:
        port = config["serial"]["port"]
        baud = config["serial"]["baudrate"]
        timeout = config["serial"].get("timeout", 1.0)
        kanaly_z_configu = config["measurement"]["channels"]
        interwal = config["measurement"]["read_interval"]
        output_dir = config["storage"]["output_dir"]
    except KeyError as e:
        logging.error(f"[Błąd Konfiguracji] Brak wymaganego klucza w JSON: {e}")
        sys.exit(1)

    device = TDCDevice(port, baud, timeout)
    logger = DataLogger(output_dir)
    
    try:
        device.connect()
    except Exception as e:
        logging.error(f"[Błąd] Brak połączenia z portem sprzętowym: {e}")
        sys.exit(1)

    pliki = logger.create_new_log_files(kanaly_z_configu)

    print("=== POMIAR WIELOKANAŁOWY TIA-V110 ===")
    print(f"Monitorowane kanały zadeklarowane w JSON: {kanaly_z_configu}")
    
    limit_input = input("\nPodaj ilość próbek do pobrania (wpisz 0 dla braku limitu): ")
    try:
        limit_probek = int(limit_input)
        if limit_probek < 0:
            raise ValueError
    except ValueError:
        limit_probek = 0
        print("Nieprawidłowa wartość, ustawiono na odczyt bez limitu.")

    print("\nNaciśnij Ctrl+C, aby zatrzymać stoper.\n")
    
    licznik = 0
    try:
        device.send_command(f"measStart {limit_probek}")
        start_time = time.time()
        
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
                            
                            # Zapis do plików TXT, bazy SQLite i bufora RAM
                            logger.append_data(pliki, odczytany_kanal, czysty_hex, parsed_val)
                            
                            sys.stdout.write(f"\r[Czas: {czas_trwania:.1f}s] Zapisano: {licznik} | Ost. sygnał CH{odczytany_kanal}: {parsed_val:.6f}       ")
                            sys.stdout.flush()
                            
                            if limit_probek > 0 and licznik >= limit_probek:
                                break
            
            # Przerwanie pętli while po osiągnięciu limitu
            if limit_probek > 0 and licznik >= limit_probek:
                print(f"\n\n[Zakończono] Osiągnięto wskazany limit próbek: {limit_probek}.")
                break
                
            time.sleep(interwal)

    except KeyboardInterrupt:
        print("\n\n[Zatrzymano] Użytkownik wcisnął Ctrl+C.")
    except Exception as e:
        print(f"\n\n[Błąd Krytyczny Pracy Pętli] {e}")
    finally:
        print("Trwa zamykanie urządzenia i zapisywanie danych...")
        device.send_command("measStop")
        device.disconnect()
        logger.close()
        print(f"Zapisano łącznie {licznik} pomiarów.")

if __name__ == "__main__":
    main()