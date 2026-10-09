import serial
import time
import threading
import logging

# Podstawowa konfiguracja logowania (możesz ją rozszerzyć w głównym pliku)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TDCDevice:
    def __init__(self, port, baudrate, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = timeout # Zabezpieczenie przed zawieszeniem zapisu
        self.ser = None
        self.lock = threading.Lock()

    def connect(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                return
                
            try:
                self.ser = serial.Serial(
                    self.port, 
                    self.baudrate, 
                    timeout=self.timeout, 
                    write_timeout=self.write_timeout
                )
                logging.info(f"[Sprzęt] Połączono z portem {self.port}")
            except serial.SerialException as e:
                logging.error(f"[Sprzęt] Nie można otworzyć portu {self.port}: {e}")
                raise ConnectionError(f"Błąd portu COM: {e}")

    def disconnect(self):
        with self.lock:
            try:
                if self.ser and self.ser.is_open:
                    self.ser.close()
                    logging.info("[Sprzęt] Rozłączono port szeregowy.")
            except Exception as e:
                logging.error(f"[Sprzęt] Błąd podczas zamykania portu: {e}")
            finally:
                self.ser = None

    def send_command(self, command, opoznienie=0.05):
        with self.lock:
            if not self.ser or not self.ser.is_open:
                logging.warning("[Sprzęt] Próba wysłania komendy do zamkniętego portu.")
                return ""
            
            try:
                komenda_z_entrem = f"{command}\n"
                self.ser.write(komenda_z_entrem.encode('utf-8'))
                
                # Wymuszamy opróżnienie bufora wyjściowego
                self.ser.flush() 
                time.sleep(opoznienie)
                
                odpowiedz = ""
                # Bezpieczny odczyt z limitem (timeout zapobiega nieskończonej pętli)
                if self.ser.in_waiting > 0:
                    surowe_bajty = self.ser.read(self.ser.in_waiting)
                    # Używamy errors='replace', aby szum z portu nie wywalił aplikacji (zastąpi krzaki znakiem '?')
                    odpowiedz = surowe_bajty.decode('utf-8', errors='replace')
                
                return odpowiedz.strip()
                
            except serial.SerialTimeoutException:
                logging.error(f"[Sprzęt] Timeout podczas zapisu komendy '{command}'.")
                self.disconnect() # Awaryjne zamknięcie
                return ""
            except serial.SerialException as e:
                logging.error(f"[Sprzęt] Utracono fizyczne połączenie z urządzeniem: {e}")
                self.disconnect() # Awaryjne zamknięcie
                return ""
            except Exception as e:
                logging.error(f"[Sprzęt] Nieoczekiwany błąd komunikacji: {e}")
                return ""

    def configure_device(self, channel, threshold, edge):
        try:
            logging.info(f"[Sprzęt] Rozpoczęto konfigurację dla kanału {channel}...")
            self.send_command("calib", opoznienie=0.5)
            self.send_command("setRefClk int")
            self.send_command("measModeTI")
            self.send_command(f"setThresh {channel} {threshold}")
            self.send_command(f"edge {channel} {edge}")
            logging.info(f"[Sprzęt] Urządzenie skonfigurowane pomyślnie dla kanału {channel}.")
        except Exception as e:
            logging.error(f"[Sprzęt] Błąd konfiguracji: {e}")