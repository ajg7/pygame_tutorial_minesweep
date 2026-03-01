import json
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any, Dict, List, Optional

BASE_URL = "https://pokeapi.co/api/v2"
USER_AGENT = "TkinterPokedex/1.0"
TIMEOUT_SECONDS = 15


class PokeAPIError(Exception):
    """Raised when the PokéAPI request fails."""



def _request(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, image/png, image/*;q=0.9, */*;q=0.8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise PokeAPIError(f"HTTP {exc.code} while requesting {url}") from exc
    except urllib.error.URLError as exc:
        raise PokeAPIError(f"Network error while requesting {url}: {exc.reason}") from exc


@lru_cache(maxsize=512)
def _get_json(url: str) -> Dict[str, Any]:
    try:
        raw = _request(url)
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise PokeAPIError(f"Invalid JSON returned from {url}") from exc


@lru_cache(maxsize=1)
def get_original_151() -> List[Dict[str, Any]]:
    """
    Fetch the original 151 Pokémon from the Kanto Pokédex.
    Returns a sorted list like:
    [{"id": 1, "name": "Bulbasaur"}, ...]
    """
    pokedex = _get_json(f"{BASE_URL}/pokedex/kanto/")
    entries = pokedex.get("pokemon_entries", [])

    pokemon = []
    for entry in entries:
        entry_number = entry.get("entry_number")
        species = entry.get("pokemon_species", {})
        name = species.get("name", "unknown")

        if isinstance(entry_number, int) and 1 <= entry_number <= 151:
            pokemon.append(
                {
                    "id": entry_number,
                    "name": name.replace("-", " ").title(),
                    "api_name": name,
                }
            )

    pokemon.sort(key=lambda p: p["id"])
    return pokemon


@lru_cache(maxsize=256)
def get_pokemon_details(pokemon_id: int) -> Dict[str, Any]:
    pokemon = _get_json(f"{BASE_URL}/pokemon/{pokemon_id}/")
    species = _get_json(f"{BASE_URL}/pokemon-species/{pokemon_id}/")

    types = [t["type"]["name"].title() for t in pokemon.get("types", [])]
    abilities = [a["ability"]["name"].replace("-", " ").title() for a in pokemon.get("abilities", [])]

    stats = {
        stat_row["stat"]["name"].replace("-", " ").title(): stat_row["base_stat"]
        for stat_row in pokemon.get("stats", [])
    }

    genera = species.get("genera", [])
    genus = next(
        (g["genus"] for g in genera if g.get("language", {}).get("name") == "en"),
        "Unknown Pokémon",
    )

    flavor_text = _pick_best_flavor_text(species.get("flavor_text_entries", []))
    sprite_url = _get_red_blue_sprite_url(pokemon)
    cry_url = _get_cry_url(pokemon)

    return {
        "id": pokemon["id"],
        "name": pokemon["name"].replace("-", " ").title(),
        "height_m": pokemon.get("height", 0) / 10,
        "weight_kg": pokemon.get("weight", 0) / 10,
        "types": types,
        "abilities": abilities,
        "stats": stats,
        "genus": genus,
        "flavor_text": flavor_text,
        "image_url": sprite_url,
        "cry_url": cry_url,
    }



def _get_red_blue_sprite_url(pokemon: Dict[str, Any]) -> Optional[str]:
    sprites = pokemon.get("sprites", {})
    version_sprites = sprites.get("versions", {}).get("generation-i", {}).get("red-blue", {})

    return version_sprites.get("front_default") or sprites.get("front_default")



def _get_cry_url(pokemon: Dict[str, Any]) -> Optional[str]:
    cries = pokemon.get("cries", {})
    return cries.get("legacy") or cries.get("latest")



def _pick_best_flavor_text(entries: List[Dict[str, Any]]) -> str:
    preferred_versions = ["red", "blue"]

    for version_name in preferred_versions:
        for entry in entries:
            if entry.get("language", {}).get("name") == "en" and entry.get("version", {}).get("name") == version_name:
                return _clean_flavor_text(entry.get("flavor_text", "No entry found."))

    for entry in entries:
        if entry.get("language", {}).get("name") == "en":
            return _clean_flavor_text(entry.get("flavor_text", "No entry found."))

    return "No Pokédex entry found."



def _clean_flavor_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").replace("\f", " ").split())


@lru_cache(maxsize=256)
def get_image_bytes(image_url: str) -> bytes:
    if not image_url:
        raise PokeAPIError("No image URL was provided.")
    return _request(image_url)
