import json
from core.device import TDCDevice
from core.logger import DataLogger
from api.app import create_api_app

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def main():
    config = load_config()
    device = TDCDevice(config["serial"]["port"], config["serial"]["baudrate"], config["serial"]["timeout"])
    logger = DataLogger(config["storage"]["output_dir"])

    try:
        device.connect()
    except Exception as e:
        print(f"[Ostrzeżenie] Problem przy starcie: {e}")

    print("=== URUCHAMIANIE SERWERA API ===")
    app = create_api_app(device, logger, config)
    
    try:
        app.run(
            host=config["api"]["host"],
            port=config["api"]["port"],
            debug=config["api"]["debug"],
            use_reloader=False
        )
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()