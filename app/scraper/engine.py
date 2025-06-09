import asyncio
import multiprocessing
from multiprocessing import Pool
from flask import Flask, request, jsonify
from .parser import (
    extract_movie_links,
    extract_serial_links,
)  # <--- ZMIANA: dodano extract_serial_links
from database.db_utils import (
    init_db,
    save_parsed_data,
)
import httpx
from bs4 import BeautifulSoup

app = Flask(__name__)

with app.app_context():
    init_db()


def process_single_movie_url(movie_url):
    """Pobiera i parsuje szczegóły pojedynczego filmu."""
    print(
        f"Proces potomny ({multiprocessing.current_process().name}) przetwarza: {movie_url}"
    )

    parsed_details = None
    try:
        response = httpx.get(movie_url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()  # Rzuci wyjątkiem dla kodów błędów HTTP
        soup = BeautifulSoup(response.content, "html.parser")

        title_element = soup.select_one("h1.name")
        title = title_element.text.strip() if title_element else None

        description_element = soup.select_one("div.w-desc.cts-wrapper > p")
        description = description_element.text.strip() if description_element else None

        if title and description:
            parsed_details = {
                "tytul": title,
                "opis": description,
                "link": movie_url,
                "typ": "film",  # Ważne dla zapisu do bazy
            }
        else:
            print(f"Nie udało się sparsować tytułu lub opisu dla: {movie_url}")

    except httpx.RequestError as e:
        print(f"Błąd żądania HTTP dla {movie_url}: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd podczas przetwarzania {movie_url}: {e}")

    if parsed_details:
        print(f"Dane sparsowane z {movie_url}: {parsed_details['tytul']}")
        save_parsed_data(parsed_details)  # Zapis do bazy danych
    else:
        print(f"Nie znaleziono danych na {movie_url}")
    return parsed_details


def process_single_serial_url(serial_url):
    """Pobiera i parsuje szczegóły pojedynczego serialu."""
    print(
        f"Proces potomny ({multiprocessing.current_process().name}) przetwarza serial: {serial_url}"
    )

    parsed_details = None
    try:
        response = httpx.get(serial_url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        title_element = soup.select_one("h1.name")
        title = title_element.text.strip() if title_element else None

        description_element = soup.select_one("div.w-desc.cts-wrapper > p")
        description = description_element.text.strip() if description_element else None

        seasons = 0
        if title:
            parsed_details = {
                "tytul": title,
                "opis": description,
                "link": serial_url,
                "sezony": seasons,
                "typ": "serial",
            }
        else:
            print(f"Nie udało się sparsować tytułu dla serialu: {serial_url}")

    except httpx.RequestError as e:
        print(f"Błąd żądania HTTP dla serialu {serial_url}: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd podczas przetwarzania serialu {serial_url}: {e}")

    if parsed_details:
        print(f"Dane sparsowane z {serial_url}: {parsed_details['tytul']}")
        save_parsed_data(parsed_details)  # Zapis do bazy danych
    else:
        print(f"Nie znaleziono danych na {serial_url}")
    return parsed_details


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method != "POST":
        return "Engine is running! Send POST request to scrape."

    data = request.get_json()
    if not data or "scrape_type" not in data:
        return jsonify({"error": "Missing 'url' or 'scrape_type' in POST data"}), 400

    scrape_type = data["scrape_type"]  # "filmy" lub "seriale"

    try:
        links_to_process = []
        process_function = None

        if scrape_type == "filmy":
            links_to_process = extract_movie_links(
                "https://braflix.club/movies", data["page"]
            )
            process_function = process_single_movie_url
        elif scrape_type == "seriale":
            links_to_process = extract_serial_links(
                "https://braflix.club/tv-shows", data["page"]
            )
            process_function = process_single_serial_url
        else:
            return jsonify({"error": f"Unknown scrape_type: {scrape_type}"}), 400

        if not links_to_process:
            return (
                jsonify({"message": f"Nie znaleziono linków dla typu: {scrape_type}."}),
                200,
            )


        scraped_data = []
        num_processes = min(6, multiprocessing.cpu_count())
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_function, links_to_process)
            for result in results:
                if result:
                    scraped_data.append(result)

        if scraped_data:
            return (
                jsonify(
                    {
                        "message": f"Scrapowanie ({scrape_type}) zakończone pomyślnie",
                        "data": scraped_data,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "message": f"Scrapowanie ({scrape_type}) zakończone, ale nie zebrano żadnych danych."
                    }
                ),
                200,
            )

    except Exception as e:
        print(f"Błąd podczas scrapowania ({scrape_type}): {e}")
        return (
            jsonify(
                {
                    "error": f"Wystąpił błąd podczas scrapowania ({scrape_type}): {str(e)}"
                }
            ),
            500,
        )


@app.route("/", methods=["POST"])  # Lub @app.route('/scrape', methods=['POST'])
def scrape_data():
    if request.method != "POST":
        return jsonify({"error": "Only POST requests are allowed"}), 405

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    scrape_type = data.get("scrape_type")
    page = data.get("page", "1")  # Pobierz numer strony, domyślnie 1

    if not scrape_type:
        return jsonify({"error": "Missing 'scrape_type' in payload"}), 400

    print(f"Engine: Rozpoczynam scrapowanie dla typu: {scrape_type}, strona: {page}")

    all_parsed_data = []
    if scrape_type == "filmy":
        # Zmodyfikuj URL_MOVIES, aby uwzględniał stronę, lub przekaż stronę do extract_movie_links
        # Przykład: movie_page_url = f"{URL_MOVIES}?page={page}"
        # movie_links = extract_movie_links(movie_page_url)
        movie_links = extract_movie_links(
            URL_MOVIES, page
        )  # Zakładamy modyfikację funkcji
        for movie_url in movie_links:
            parsed_info = process_single_movie_url(movie_url)
            if parsed_info:
                all_parsed_data.append(parsed_info)
        save_parsed_data(all_parsed_data, "filmy")

    elif scrape_type == "seriale":
        # Zmodyfikuj URL_SERIES, aby uwzględniał stronę, lub przekaż stronę do extract_serial_links
        # Przykład: serial_page_url = f"{URL_SERIES}?page={page}"
        # serial_links = extract_serial_links(serial_page_url)
        serial_links = extract_serial_links(
            URL_SERIES, page
        )  # Zakładamy modyfikację funkcji
        for serial_url in serial_links:
            parsed_info = process_single_serial_url(serial_url)
            if parsed_info:
                all_parsed_data.append(parsed_info)
        save_parsed_data(all_parsed_data, "seriale")
    else:
        print(f"Engine: Nieznany typ scrapowania: {scrape_type}")
        return jsonify({"error": f"Unknown scrape_type: {scrape_type}"}), 400

    print(
        f"Engine: Zakończono scrapowanie. Zapisano {len(all_parsed_data)} elementów typu '{scrape_type}' ze strony {page}."
    )
    return jsonify(all_parsed_data)


if __name__ == "__main__":
    # Uruchomienie przez `python -m scraper.engine` lub bezpośrednio
    # init_db() jest już wywoływane w kontekście aplikacji powyżej
    app.run(
        host="0.0.0.0", port=5001, debug=False
    )  # debug=False dla produkcji/Gunicorn
