from flask import Flask, jsonify, request
import threading
import time
import re

# Funkcje pomocnicze skopiowane ze stopera, aby API mogło samodzielnie parsować paczki
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
    resp = device.send_command("dataCNT", opoznienie=0.01)
    if resp:
        match = re.search(r'\d+', resp)
        if match:
            return int(match.group())
    return 0

def create_api_app(device, logger, config):
    app = Flask(__name__)
    
    # Stan pomiaru przystosowany do pracy wielokanałowej
    measurement_state = {
        "is_running": False,
        "current_files_map": None,
        "latest_values": {},  # np. {1: 123.45, 2: 678.90}[cite: 10]
        "limit": 0,
        "count": 0
    }
    
    stop_event = threading.Event()

    def background_measurement_loop(channels, interval, limit):
        print("[API] Uruchomiono wątek pomiarowy w tle.")
        licznik = 0
        
        while not stop_event.is_set():
            try:
                # 1. Sprawdzamy ilość próbek
                ilosc_w_buforze = get_data_count(device)
                
                # 2. Pobieramy je wszystkie na raz, jeśli istnieją
                if ilosc_w_buforze > 0:
                    raw_response = device.send_command(f"dataRd {ilosc_w_buforze} hex", opoznienie=0.05)
                    
                    if raw_response:
                        pomiary = parse_raw_data(raw_response)
                        
                        for ch, val, raw in pomiary:
                            if ch in channels:
                                licznik += 1
                                measurement_state["latest_values"][ch] = val
                                measurement_state["count"] = licznik
                                
                                # Przesyłanie wyników jednocześnie do TXT i na "eter" API
                                if measurement_state["current_files_map"]:
                                    logger.append_data(measurement_state["current_files_map"], ch, raw, val)
                                
                                # Zatrzymanie przy limitach
                                if limit > 0 and licznik >= limit:
                                    break
                
                # Sprawdzenie po pętli czy osiągnięto limit
                if limit > 0 and licznik >= limit:
                    print(f"[API] Osiągnięto limit pomiarów ({limit}). Zatrzymywanie...")
                    break
                    
            except Exception as e:
                print(f"[Błąd Wątku API] {e}")[cite: 10]
                
            time.sleep(interval)
            
        # Zatrzymywanie sprzętu przy wyjściu z pętli
        measurement_state["is_running"] = False
        device.send_command("measStop")
        print("[API] Wątek pomiarowy w tle został zatrzymany.")[cite: 10]

    @app.route("/device/status", methods=["GET"])
    def get_status():
        return jsonify({
            "isMeasuring": measurement_state["is_running"],
            "latestValues": measurement_state["latest_values"],
            "totalCount": measurement_state["count"]
        }), 200

    @app.route("/device/data", methods=["GET"])
    def get_data():
        """Nowy endpoint konsumujący dane z 'eteru' w loggerze na bieżąco."""
        channels = config["measurement"]["channels"]
        response_data = {}
        for ch in channels:
            # Pobiera wszystkie wygenerowane próbki od ostatniego zapytania na ten adres
            response_data[ch] = logger.consume_api_stream(ch)
        return jsonify(response_data), 200

    @app.route("/device/start", methods=["POST"])
    def start_measurement():
        if measurement_state["is_running"]:
            return jsonify({"error": "Pomiar już trwa!"}), 400

        try:
            # API pobiera teraz opcjonalny limit przesyłany w ciele zapytania JSON (np. {"limit": 100})
            req_data = request.get_json(silent=True) or {}
            limit = req_data.get("limit", 0)

            device.send_command(f"measStart {limit}")
            channels = config["measurement"]["channels"]
            
            measurement_state["current_files_map"] = logger.create_new_log_files(channels)
            measurement_state["is_running"] = True
            measurement_state["limit"] = limit
            measurement_state["count"] = 0
            measurement_state["latest_values"] = {}
            
            stop_event.clear()
            t = threading.Thread(
                target=background_measurement_loop, 
                args=(channels, config["measurement"]["read_interval"], limit),
                daemon=True
            )
            t.start()
            
            return jsonify({
                "message": f"Pomiar uruchomiony pomyślnie (limit: {limit})",
                "files": measurement_state["current_files_map"]
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/device/stop", methods=["POST"])
    def stop_measurement():
        if not measurement_state["is_running"]:
            return jsonify({"error": "Pomiar nie jest uruchomiony!"}), 400

        # Wątek złapie ten sygnał, zakończy pętlę i zrzuci "measStop" do samego urządzenia
        stop_event.set() 
        
        return jsonify({"message": "Zlecono zatrzymanie pomiaru"}), 200

    return app