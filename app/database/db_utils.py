import sqlite3
import os

# Domyślna ścieżka do bazy danych w kontenerze Docker
# Może być nadpisana przez zmienną środowiskową, jeśli zajdzie taka potrzeba
DEFAULT_DB_PATH = "/usr/src/app/data/scraped_data.db"


def get_db_connection():
    db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
    # Upewnij się, że katalog dla pliku bazy danych istnieje
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwie
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela dla filmów
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS filmy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tytul VARCHAR(255) NOT NULL,
            opis TEXT,
            link VARCHAR(255),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Tabela dla seriali
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS seriale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tytul VARCHAR(255) NOT NULL,
            opis TEXT,
            sezony INTEGER,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()
    print("Database initialized with 'filmy' and 'seriale' tables.")


# Funkcja do zapisywania danych - teraz trzeba będzie ją dostosować
# lub stworzyć osobne funkcje dla filmów i seriali
def save_parsed_data(item):
    """
    Zapisuje sparsowane dane do odpowiedniej tabeli.
    'parsed_items' powinien być listą słowników, gdzie każdy słownik
    reprezentuje jeden element (film lub serial) i zawiera klucze
    odpowiadające kolumnom w tabeli (np. 'tytul', 'opis', 'link'/'sezony').
    Dodatkowo, potrzebujemy informacji, do której tabeli zapisać dane.
    Można to rozwiązać np. przez dodanie klucza 'typ' ('film'/'serial')
    do każdego słownika w parsed_items.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Przykład: rozróżnianie na podstawie dodatkowego pola 'typ' w parsed_item
    # Należy dostosować logikę w scraperze, aby dodawał to pole.
    item_type = item.get("typ")  # Załóżmy, że scraper dodał pole 'typ'
    if item_type == "film":
        cursor.execute(
            """
            INSERT INTO filmy (tytul, opis, link) 
            VALUES (?, ?, ?)
        """,
            (item.get("tytul"), item.get("opis"), item.get("link")),
        )
    elif item_type == "serial":
        cursor.execute(
            """
            INSERT INTO seriale (tytul, opis, sezony) 
            VALUES (?, ?, ?)
        """,
            (item.get("tytul"), item.get("opis"), item.get("sezony")),
        )
    else:
        print(f"Nieznany typ danych: {item_type} dla {item.get('tytul')}")

    conn.commit()
    conn.close()
    print(f"Saved {item} items to the database.")


def get_all_filmy():
    """Pobiera wszystkie filmy z tabeli 'filmy'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, tytul, opis, link, scraped_at FROM filmy ORDER BY scraped_at DESC"
    )
    filmy = cursor.fetchall()
    conn.close()

    return [dict(row) for row in filmy]


def get_all_seriale():
    """Pobiera wszystkie seriale z tabeli 'seriale'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, tytul, opis, sezony, scraped_at FROM seriale ORDER BY scraped_at DESC"
    )
    seriale = cursor.fetchall()
    conn.close()

    return [dict(row) for row in seriale]


if __name__ == "__main__":
    print(f"Initializing database at: {os.getenv('DB_PATH', DEFAULT_DB_PATH)}")
    init_db()
