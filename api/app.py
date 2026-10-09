import sqlite3
from flask import Flask, jsonify, render_template

def create_api_app(logger, config):
    app = Flask(__name__, template_folder='templates')

    @app.route('/')
    def index():
        # Renderowanie lokalnego dashboardu i przekazanie listy aktywnych kanałów
        kanaly = config["measurement"]["channels"]
        return render_template('index.html', channels=kanaly)

    @app.route('/api/status')
    def api_status():
        # Prosty endpoint dla zewnętrznego serwera sprawdzający czy komputer żyje
        return jsonify({
            "status": "online",
            "konfiguracja": config["measurement"]
        })

    @app.route('/api/dane/<int:kanal>')
    def api_pobierz_dane(kanal):
        # Pobieranie 15 ostatnich pomiarów z lokalnej bazy danych SQLite
        wyniki = []
        try:
            # Otwieramy nowe połączenie z bazą, bezpieczne dla wątków Flaska
            conn = sqlite3.connect(logger.db_path)
            cursor = conn.cursor()
            
            # Pobieramy najnowsze wpisy dla konkretnego kanału
            cursor.execute(
                "SELECT timestamp, raw_data, parsed_value FROM pomiary WHERE channel = ? ORDER BY id DESC LIMIT 15",
                (kanal,)
            )
            
            for row in cursor.fetchall():
                wyniki.append({
                    "timestamp": row[0],
                    "raw_hex": row[1],
                    "wartosc": float(row[2]) if row[2] else 0.0
                })
            conn.close()
        except Exception as e:
            return jsonify({"error": f"Błąd odczytu bazy: {e}"}), 500

        return jsonify({"kanal": kanal, "dane": wyniki})

    return app