# Kanto Pokédex (Tkinter)

A small desktop **Pokédex** app built with **Python + Tkinter**.

It pulls data from **PokéAPI** (https://pokeapi.co/) to show the original **Kanto Pokédex (#001–#151)**, including:

- Gen I-style sprite
- Pokédex flavor text
- Types, abilities, and base stats
- A “Cry” button that downloads the cry audio and opens it in your system’s default audio player

> Note: The folder name mentions “minesweeper/pygame”, but this codebase is a **Tkinter Pokédex**.

---

## Quick start

### 1) Requirements

- Python 3.9+ (3.10+ recommended)
- Internet connection (PokéAPI requests)

Optional (recommended):

- `Pillow` for higher-quality image loading/scaling

### 2) Run

From the project folder:

```bash
python main.py
```

If you prefer using a virtual environment, that works too (not required).

### 3) Optional dependency (Pillow)

If you want the app to use PIL for image decode/resize:

```bash
python -m pip install pillow
```

Without Pillow, the app falls back to `tk.PhotoImage` for PNG rendering.

---

## How to use the app

- **Select a Pokémon** from the list on the right to load its entry.
- **Search** by name or number in the search field (e.g. `pikachu`, `25`).
- Use **PREV / NEXT** to move through the filtered list.
- Click **♪ CRY** to download the Pokémon’s cry and open it with your OS audio player.

---

## Project navigation (code tour)

If you’re trying to understand or modify the project, start here:

- `main.py`
  - The entry point. Calls `main()` from `app.py`.

- `app.py`
  - The main Tkinter UI.
  - Contains the `PokedexApp` class (layout, event handlers, background threads).
  - Handles:
    - Building the left/right Pokédex shell UI
    - Loading the list of the original 151 Pokémon
    - Filtering by search text
    - Loading details + sprite bytes in a worker thread
    - Rendering the sprite and text into the UI

- `pokeapi_client.py`
  - All PokéAPI access (HTTP + JSON parsing) with caching.
  - Key functions:
    - `get_original_151()` → list for the Kanto index
    - `get_pokemon_details(pokemon_id)` → details used by the UI
    - `get_image_bytes(url)` → downloads sprite PNG

- `cry_player.py`
  - Downloads cry audio to a temp folder and opens it using the OS default handler.
  - Cross-platform launch (`os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux).

- `ui_utils.py`
  - Small UI helpers:
    - `set_readonly_text()` to safely update `tk.Text` widgets
    - `image_bytes_to_photoimage()` to convert downloaded PNG bytes into a Tkinter-displayable image

- `shell_styles.py`
  - Centralized style constants (colors, window size, font tuples).

---

## Troubleshooting

- **“Could not load Pokémon list/details”**
  - Usually a network issue (no internet, firewall, PokéAPI downtime).

- **Sprite doesn’t display**
  - Try installing Pillow (`python -m pip install pillow`).
  - Some environments can be picky about PNG handling via `tk.PhotoImage`.

- **Cry button doesn’t play audio**
  - The app _downloads_ the cry and then asks your OS to open the file.
  - Make sure you have an application associated with `.ogg` files.

---

## Credits

- Data and sprites are provided by **PokéAPI** (https://pokeapi.co/).
