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
    
def get_season_episodes(tmdb_id, season_number):
    url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/season/{season_number}"

    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json"
    }

    params = {
        "language": "pt-PT"
    }

    response = requests.get(url, headers=headers, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()

    episodes = data.get("episodes", [])

    result = []

    for ep in episodes:
        result.append({
            "season": season_number,
            "episode": ep.get("episode_number"),
            "title": ep.get("name")
        })

    return result
import time

def get_tv_details(tmdb_id):
    url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"

    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json"
    }

    params = {"language": "pt-PT"}

    response = requests.get(url, headers=headers, params=params, timeout=5)
    response.raise_for_status()

    return response.json()