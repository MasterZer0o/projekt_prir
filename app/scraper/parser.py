import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://braflix.club"


def extract_movie_links(category_url: str, page: str = '1') -> list:
    target_url = f"{category_url}?page={page}" # Dostosuj parametr URL do paginacji strony docelowej
                                              # Może to być np. ?page=, /page/, itp.
    print(f"Pobieranie linków do filmów z: {target_url}")
    try:
        response = httpx.get(target_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        movie_links = []
        for link_tag in soup.select(
            "body > div:nth-child(3) > div.flex-1 > div > div > div:nth-child(3) a"
        ):
            href = link_tag.get("href")
            movie_links.append(href)

        print(f"Znaleziono {len(movie_links)} linków do filmów na stronie {category_url}")
        return movie_links

    except httpx.RequestError as exc:
        print(f"Wystąpił błąd żądania HTTP: {exc}")
        return []


def extract_serial_links(category_url: str, page: str = '1') -> list:
    """Pobiera linki do poszczególnych seriali z podanej strony kategorii i numeru strony."""
    target_url = f"{category_url}?page={page}" # Dostosuj parametr URL do paginacji strony docelowej
    print(f"Rozpoczynam pobieranie linków do seriali z: {target_url}")
    try:
        response = httpx.get(target_url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        serial_links = []

        for link_tag in soup.select(
            "body > div:nth-child(3) > div.flex-1 > div > div > div:nth-child(3) a"
        ):
            href = link_tag.get("href")
            if href:  # Only add if href exists
                serial_links.append(href)

        print(f"Znaleziono {len(serial_links)} linków do seriali.")
        return list(set(serial_links))
    except httpx.RequestError as exc:
        print(f"Wystąpił błąd żądania HTTP podczas pobierania {category_url}: {exc}")
        return []
    except Exception as e:
        print(
            f"Nieoczekiwany błąd podczas pobierania linków do seriali z {category_url}: {e}"
        )
        return []
