import json
from core.device import TDCDevice

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def main():
    print("=== Inicjalizacja i Konfiguracja TDC ===")
    config = load_config()
    device = TDCDevice(config["serial"]["port"], config["serial"]["baudrate"], config["serial"]["timeout"])
    
    try:
        device.connect()
        
        # Konfiguracja globalna
        device.send_command("calib", opoznienie=0.5)
        device.send_command("setRefClk int")
        device.send_command("measModeTI")
        
        # Konfiguracja każdego kanału z listy JSON
        kanaly = config["measurement"]["channels"]
        prog = config["measurement"]["threshold"]
        zbocze = config["measurement"]["edge"]
        
        for kanal in kanaly:
            device.send_command(f"setThresh {kanal} {prog}")
            device.send_command(f"edge {kanal} {zbocze}")
            print(f"Skonfigurowano wejście {kanal} (próg: {prog}V, zbocze: {zbocze})")
            
        print("\n[Sukces] Urządzenie gotowe do pomiarów wielokanałowych.")
    except Exception as e:
        print(f"\n[Błąd] {e}")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()