import os
import sqlite3
import logging
from datetime import datetime

class DataLogger:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        
        # Zabezpieczenie przed błędem tworzenia folderu
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                logging.error(f"[Logger] Nie można utworzyć folderu {output_dir}: {e}")
                
        # Struktura przygotowana pod API
        self.api_data_stream = {}
        
        # Uchwyty do otwartych plików (dla stałego strumieniowania)
        self.file_handles = {}

        # Konfiguracja lokalnej bazy danych SQLite dla logowania hybrydowego
        self.db_path = os.path.join(self.output_dir, "baza_lokalna.db")
        try:
            # check_same_thread=False pozwala API i CLI używać bazy równolegle
            self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._init_db()
        except Exception as e:
            logging.error(f"[Logger] Błąd inicjalizacji bazy SQLite: {e}")
            self.db_conn = None

    def _init_db(self):
        """Inicjalizuje tabelę w bazie SQLite, jeśli jeszcze nie istnieje."""
        if self.db_conn:
            with self.db_conn:
                self.db_conn.execute('''
                    CREATE TABLE IF NOT EXISTS pomiary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        channel INTEGER,
                        raw_data TEXT,
                        parsed_value TEXT
                    )
                ''')

    def create_new_log_files(self, channels):
        """Tworzy pliki dla każdego kanału i zwraca słownik ścieżek."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_map = {}
        
        for ch in channels:
            raw_filepath = os.path.join(self.output_dir, f"pomiar_raw_{timestamp}_input_{ch}.txt")
            parsed_filepath = os.path.join(self.output_dir, f"pomiar_przeliczone_{timestamp}_input_{ch}.txt")
            
            try:
                # Otwieramy pliki i pozostawiamy je otwarte
                f_raw = open(raw_filepath, 'a', encoding='utf-8')
                f_parsed = open(parsed_filepath, 'a', encoding='utf-8')
                
                f_raw.write(f"SUROWE DANE (HEX) - INPUT {ch}\n" + "-" * 40 + "\n")
                f_parsed.write(f"PRZELICZONA WARTOSC - INPUT {ch}\n" + "-" * 40 + "\n")
                
                # Przechowujemy uchwyty plików do zapisu strumieniowego
                self.file_handles[ch] = {"raw": f_raw, "parsed": f_parsed}
                
                files_map[ch] = {
                    "raw": raw_filepath,
                    "parsed": parsed_filepath
                }
                
                # Inicjalizacja pustej kolejki dla danego kanału
                self.api_data_stream[ch] = []
                
            except Exception as e:
                logging.error(f"[Logger] Błąd tworzenia plików dla kanału {ch}: {e}")
                
        return files_map

    def append_data(self, files_map, channel, raw_data, parsed_value):
        """Dopisuje dane na bieżąco do plików TXT, SQLite i wysyła do bufora dla API."""
        if channel not in self.file_handles:
            return 
            
        handles = self.file_handles[channel]
        timestamp_iso = datetime.now().isoformat()
        
        # 1. Zapis klasyczny (strumieniowanie z wymuszonym zrzutem z bufora dyskowego)
        try:
            handles["raw"].write(f"{raw_data}\n")
            handles["raw"].flush()
            
            handles["parsed"].write(f"{parsed_value:.6f}\n")
            handles["parsed"].flush()
        except Exception as e:
            logging.error(f"[Logger] Błąd zapisu do pliku: {e}")

        # 2. Zapis do hybrydowej bazy SQLite
        if self.db_conn:
            try:
                with self.db_conn:
                    self.db_conn.execute(
                        "INSERT INTO pomiary (channel, raw_data, parsed_value) VALUES (?, ?, ?)",
                        (channel, raw_data, str(parsed_value))
                    )
            except Exception as e:
                logging.error(f"[Logger] Błąd zapisu do SQLite: {e}")
                
        # 3. Emisja w "eter" (bufor w pamięci RAM do wykorzystania przez moduł API)
        if channel in self.api_data_stream:
            self.api_data_stream[channel].append({
                "timestamp": timestamp_iso,
                "raw": raw_data,
                "value": str(parsed_value) # Konwersja Decimal na String dla bezpieczeństwa JSON w API
            })

    def consume_api_stream(self, channel):
        """Metoda dla zewnętrznego modułu API - pobiera i czyści bieżący strumień z pamięci."""
        if channel in self.api_data_stream:
            data = self.api_data_stream[channel]
            self.api_data_stream[channel] = []  # Czyszczenie odebranych danych
            return data
        return []

    def close(self):
        """Zamyka otwarte strumienie i bazę na wypadek wyłączenia programu."""
        for handles in self.file_handles.values():
            try:
                handles["raw"].close()
                handles["parsed"].close()
            except Exception:
                pass
        
        if self.db_conn:
            try:
                self.db_conn.close()
            except Exception:
                pass