import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "TkinterPokedex/1.0"
TIMEOUT_SECONDS = 15


class CryPlaybackError(Exception):
    """Raised when a cry cannot be downloaded or opened."""



def _download_cry(cry_url: str, pokemon_id: int, pokemon_name: str) -> Path:
    if not cry_url:
        raise CryPlaybackError("No cry URL is available for this Pokémon.")

    request = urllib.request.Request(cry_url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise CryPlaybackError(f"HTTP {exc.code} while downloading cry.") from exc
    except urllib.error.URLError as exc:
        raise CryPlaybackError(f"Network error while downloading cry: {exc.reason}") from exc

    safe_name = "".join(char for char in pokemon_name.lower() if char.isalnum() or char in ("-", "_")) or "pokemon"
    target_dir = Path(tempfile.gettempdir()) / "tkinter_pokedex_cries"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{pokemon_id:03}_{safe_name}.ogg"
    target_file.write_bytes(data)
    return target_file



def _open_file(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:  # broad on purpose for cross-platform launch issues
        raise CryPlaybackError(f"Could not open audio player: {exc}") from exc



def play_pokemon_cry(cry_url: str, pokemon_id: int, pokemon_name: str) -> Path:
    cry_file = _download_cry(cry_url, pokemon_id, pokemon_name)
    _open_file(cry_file)
    return cry_file
