import os
from datetime import datetime

class DataLogger:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Struktura przygotowana pod API - przechowuje najnowsze odczyty z "eteru"
        self.api_data_stream = {}

    def create_new_log_files(self, channels):
        """Tworzy pliki dla każdego kanału i zwraca słownik ścieżek."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_map = {}
        
        for ch in channels:
            raw_filename = f"pomiar_raw_{timestamp}_input_{ch}.txt"
            parsed_filename = f"pomiar_przeliczone_{timestamp}_input_{ch}.txt"
            
            raw_filepath = os.path.join(self.output_dir, raw_filename)
            parsed_filepath = os.path.join(self.output_dir, parsed_filename)
            
            with open(raw_filepath, 'w') as f_raw:
                f_raw.write(f"SUROWE DANE (HEX) - INPUT {ch}\n")
                f_raw.write("-" * 40 + "\n")
                
            with open(parsed_filepath, 'w') as f_parsed:
                f_parsed.write(f"PRZELICZONA WARTOSC - INPUT {ch}\n")
                f_parsed.write("-" * 40 + "\n")
            
            files_map[ch] = {
                "raw": raw_filepath,
                "parsed": parsed_filepath
            }
            
            # Inicjalizacja pustej kolejki dla danego kanału
            self.api_data_stream[ch] = []
            
        return files_map

    def append_data(self, files_map, channel, raw_data, parsed_value):
        """Dopisuje dane na bieżąco do plików TXT i wysyła do bufora dla API."""
        if channel not in files_map:
            return 
            
        paths = files_map[channel]
        
        # 1. Zapis klasyczny (do plików)
        with open(paths["raw"], 'a') as f_raw:
            f_raw.write(f"{raw_data}\n")
            
        with open(paths["parsed"], 'a') as f_parsed:
            f_parsed.write(f"{parsed_value:.6f}\n")
            
        # 2. Emisja w "eter" (bufor w pamięci RAM do wykorzystania przez moduł API)
        if channel in self.api_data_stream:
            self.api_data_stream[channel].append({
                "timestamp": datetime.now().isoformat(),
                "raw": raw_data,
                "value": parsed_value
            })

    def consume_api_stream(self, channel):
        """Metoda dla zewnętrznego modułu API - pobiera i czyści bieżący strumień z pamięci."""
        if channel in self.api_data_stream:
            data = self.api_data_stream[channel]
            self.api_data_stream[channel] = []  # Czyszczenie odebranych danych
            return data
        return []