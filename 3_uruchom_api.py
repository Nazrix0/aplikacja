import json
import logging
from core.logger import DataLogger
from api.app import create_api_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print("==========================================")
    print("    URUCHAMIANIE LOKALNEGO SERWERA API    ")
    print("==========================================")
    
    config = load_config()
    
    # Inicjalizujemy logger tylko po to, by uzyskać poprawną ścieżkę do bazy SQLite
    logger = DataLogger(config["storage"]["output_dir"])

    app = create_api_app(logger, config)
    
    # Uruchomienie na porcie z configu (domyślnie 5000)
    # host="0.0.0.0" oznacza, że API będzie widoczne w sieci VPN
    app.run(
        host=config["api"]["host"],
        port=config["api"]["port"],
        debug=config["api"]["debug"],
        use_reloader=False
    )

if __name__ == "__main__":
    main()