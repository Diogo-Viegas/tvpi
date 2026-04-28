import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_TOKEN = os.getenv("TMDB_TOKEN")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def search_tv_show(query):
    if not TMDB_TOKEN:
        raise Exception("TMDB_TOKEN não definido no .env")

    url = f"{TMDB_BASE_URL}/search/tv"

    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json"
    }

    params = {
        "query": query,
        "language": "pt-PT"
    }

    response = requests.get(url, headers=headers, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if not results:
        return None

    show = results[0]

    poster_url = None
    if show.get("poster_path"):
        poster_url = TMDB_IMAGE_BASE + show["poster_path"]

    return {
        "tmdb_id": show.get("id"),
        "title": show.get("name"),
        "overview": show.get("overview"),
        "poster_url": poster_url,
        "first_air_date": show.get("first_air_date")
    }