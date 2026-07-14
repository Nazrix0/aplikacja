import serial
import time
import threading
import re

class TDCDevice:
    def __init__(self, port, baudrate, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.lock = threading.Lock()

    def connect(self):
        with self.lock:
            if not self.ser or not self.ser.is_open:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                print(f"[Sprzęt] Połączono z portem {self.port}")

    def disconnect(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("[Sprzęt] Rozłączono port szeregowy")

    def send_command(self, command, opoznienie=0.05):
        with self.lock:
            if not self.ser or not self.ser.is_open:
                raise ConnectionError("Port szeregowy jest zamknięty!")
            
            komenda_z_entrem = f"{command}\n"
            self.ser.write(komenda_z_entrem.encode('utf-8'))
            time.sleep(opoznienie)
            
            odpowiedz = ""
            while self.ser.in_waiting > 0:
                odpowiedz += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='replace')
            
            return odpowiedz.strip()

    def configure_device(self, channel, threshold, edge):
        print("[Sprzęt] Konfiguracja urządzenia...")
        self.send_command("calib", opoznienie=0.5)
        self.send_command("setRefClk int")
        self.send_command("measModeTI")
        self.send_command(f"setThresh {channel} {threshold}")
        self.send_command(f"edge {channel} {edge}")
        print("[Sprzęt] Urządzenie skonfigurowane pomyślnie.")

    def parse_raw_data(self,raw_string):
        """
        Parsuje surowy ciąg HEX z urządzenia za pomocą regex i wylicza czas.
        Oczekiwany format: [kanał] [event_cnt] [ts_cnt] [ts_fine]
        Np.: 01 000000A2 00000000ABCD 01FA
        """
        # Regex szuka dokładnie 4 grup znaków szesnastkowych o konkretnych długościach:
        # 1. Kanał (2 znaki)
        # 2. Event Counter (8 znaków)
        # 3. ts_cnt (12 znaków)
        # 4. ts_fine (4 znaki)
        pattern = r"([0-9A-Fa-f]{2})\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{12})\s+([0-9A-Fa-f]{4})"
        
        match = re.search(pattern, raw_string)
        
        if match:
            try:
                # Pobieranie grup i konwersja z formatu HEX (baza 16) na liczby całkowite
                channel = int(match.group(1), 16)       # (Opcjonalnie do logowania)
                event_cnt = int(match.group(2), 16)     # (Opcjonalnie do logowania)
                ts_cnt = int(match.group(3), 16)
                ts_fine = int(match.group(4), 16)
                
                # Przeliczenie matematyczne według podanego wzoru
                parsed_value = (ts_cnt + (ts_fine / (2 ** 14))) * (1 / 0.55)
                
                return parsed_value
                
            except ValueError:
                # Zabezpieczenie na wypadek, gdyby konwersja się nie udała
                return None
        else:
            # Jeśli ciąg znaków nie pasuje do wzorca (np. błąd UART)
            return None