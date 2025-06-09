import os
import httpx
import requests
from flask import Blueprint, render_template, jsonify, request  # Dodano request
import httpx
import os

# Użyj absolutnego importu, jeśli struktura projektu na to pozwala i jest poprawnie skonfigurowana
from app.database.db_utils import (
    get_all_filmy,
    get_all_seriale,
    init_db,
)  # Dodano get_all_seriale

main_blueprint = Blueprint("main", __name__)

ENGINE_API_URL = os.getenv("ENGINE_API_URL", "http://engine:5001")
DB_PATH = os.getenv("DB_PATH", "data/scraped_data.db")


@main_blueprint.route("/")
def index():
    # Inicjalizacja bazy danych przy pierwszym uruchomieniu, jeśli to konieczne
    # init_db() # Można to przenieść do app.py lub entrypoint.sh, aby wykonało się raz
    return render_template("index.html")


@main_blueprint.route('/get_data', methods=['GET'])
def get_data_route():
    scrape_type = request.args.get('type', 'filmy')
    page = request.args.get('page', '1') # Pobierz numer strony, domyślnie 1
    try:
        # Tutaj logika pobierania danych z bazy może wymagać modyfikacji,
        # jeśli chcesz filtrować dane z bazy po stronie.
        # Na razie zakładamy, że get_all_filmy/seriale zwracają wszystko,
        # a paginacja dotyczy głównie scrapowania.
        if scrape_type == 'filmy':
            data = get_all_filmy() # Można dodać logikę paginacji dla danych z bazy
        elif scrape_type == 'seriale':
            data = get_all_seriale() # Można dodać logikę paginacji dla danych z bazy
        else:
            return jsonify({"error": "Nieznany typ danych"}), 400
        return jsonify(data)
    except Exception as e:
        print(f"Błąd podczas pobierania danych z bazy dla typu '{scrape_type}', strona '{page}': {e}")
        return jsonify({"error": f"Błąd serwera podczas pobierania danych: {str(e)}"}), 500

@main_blueprint.route('/start_scrape', methods=['POST'])
def start_scrape_route():
    scrape_type = request.args.get('type', 'filmy')
    page = request.args.get('page', '1') # Pobierz numer strony
    print(f"Otrzymano żądanie scrapowania dla typu: {scrape_type}, strona: {page}")
    try:
        payload = {"scrape_type": scrape_type, "page": page} # Dodaj stronę do payloadu
        with httpx.Client(timeout=60.0) as client:
            response = client.post(ENGINE_API_URL, json=payload)
            response.raise_for_status()
        
        scraped_data = response.json()
        print(f"Dane otrzymane z silnika dla typu '{scrape_type}', strona '{page}': {len(scraped_data)} elementów")
        return jsonify(scraped_data)
    except httpx.ReadTimeout:
        print(f"Timeout podczas komunikacji z engine dla typu '{scrape_type}', strona '{page}'")
        return jsonify({"error": "Przekroczono limit czasu odpowiedzi od serwisu scrapującego."}), 504
    except httpx.HTTPStatusError as e:
        print(f"Błąd HTTP podczas komunikacji z engine dla typu '{scrape_type}', strona '{page}': {e.response.status_code} - {e.response.text}")
        return jsonify({"error": f"Błąd serwisu scrapującego: {e.response.status_code}", "details": e.response.text}), e.response.status_code
    except Exception as e:
        print(f"Nieoczekiwany błąd w start_scrape_route dla typu '{scrape_type}', strona '{page}': {e}")
        return jsonify({"error": f"Wystąpił nieoczekiwany błąd: {str(e)}"}), 500
