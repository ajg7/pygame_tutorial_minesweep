import threading
import tkinter as tk
from typing import Any, Dict, List, Optional

from cry_player import CryPlaybackError, play_pokemon_cry
from pokeapi_client import PokeAPIError, get_image_bytes, get_original_151, get_pokemon_details
from shell_styles import Fonts, ShellStyle
from ui_utils import image_bytes_to_photoimage, set_readonly_text


class PokedexApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(ShellStyle.WINDOW_TITLE)
        self.root.geometry(ShellStyle.WINDOW_SIZE)
        self.root.minsize(ShellStyle.MIN_WIDTH, ShellStyle.MIN_HEIGHT)
        self.root.configure(bg=ShellStyle.WINDOW_BG)

        self.all_pokemon: List[Dict[str, Any]] = []
        self.filtered_pokemon: List[Dict[str, Any]] = []
        self.current_details: Optional[Dict[str, Any]] = None
        self.current_photo: Optional[tk.PhotoImage] = None
        self.current_image_data: Optional[bytes] = None

        self.name_var = tk.StringVar(value="BOOTING...")
        self.meta_var = tk.StringVar(value="Initializing Kanto registry")
        self.type_var = tk.StringVar(value="Types: --")
        self.ability_var = tk.StringVar(value="Abilities: --")
        self.status_var = tk.StringVar(value="Connecting to Professor Oak's network...")
        self.search_var = tk.StringVar()

        self._build_ui()
        self._set_idle_content()
        self._load_pokemon_list()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        shell = tk.Frame(
            self.root,
            bg=ShellStyle.SHELL_RED,
            highlightbackground="#5E1010",
            highlightthickness=6,
            bd=0,
        )
        shell.grid(row=0, column=0, padx=18, pady=18, sticky="nsew")
        shell.columnconfigure(0, weight=ShellStyle.LEFT_WEIGHT)
        shell.columnconfigure(1, weight=0)
        shell.columnconfigure(2, weight=ShellStyle.RIGHT_WEIGHT, minsize=ShellStyle.RIGHT_MIN_WIDTH)
        shell.rowconfigure(0, weight=1)

        self._build_left_half(shell)
        self._build_hinge(shell)
        self._build_right_half(shell)

    def _build_left_half(self, parent: tk.Frame) -> None:
        left = tk.Frame(parent, bg=ShellStyle.SHELL_RED, padx=18, pady=16)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=5, minsize=300)
        left.rowconfigure(3, weight=1, minsize=180)

        top = tk.Frame(left, bg=ShellStyle.SHELL_RED)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(1, weight=1)

        lens_canvas = tk.Canvas(top, width=92, height=92, bg=ShellStyle.SHELL_RED, highlightthickness=0)
        lens_canvas.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
        lens_canvas.create_oval(6, 6, 86, 86, fill="#D8F0FF", outline="#EAF8FF", width=3)
        lens_canvas.create_oval(18, 18, 74, 74, fill=ShellStyle.BUTTON_BLUE, outline="#B9E1FF", width=5)
        lens_canvas.create_oval(28, 28, 45, 45, fill="#D9F4FF", outline="")

        lights = tk.Frame(top, bg=ShellStyle.SHELL_RED)
        lights.grid(row=0, column=1, sticky="nw")
        for color in ("#FF6B6B", "#FFD93D", "#6BCB77"):
            light = tk.Canvas(lights, width=24, height=24, bg=ShellStyle.SHELL_RED, highlightthickness=0)
            light.pack(side="left", padx=4)
            light.create_oval(4, 4, 20, 20, fill=color, outline="#F3F3F3", width=1)

        brand = tk.Label(
            top,
            text="POKéDEX",
            bg=ShellStyle.SHELL_RED,
            fg="#FFF7F0",
            font=Fonts.BRAND,
        )
        brand.grid(row=1, column=1, sticky="sw")

        screen_bezel = tk.Frame(
            left,
            bg=ShellStyle.BEZEL,
            highlightbackground="#EAEAEA",
            highlightthickness=2,
            padx=18,
            pady=18,
        )
        screen_bezel.grid(row=1, column=0, sticky="nsew", pady=(4, 14))
        screen_bezel.columnconfigure(0, weight=1)
        screen_bezel.rowconfigure(1, weight=1)

        screen_header = tk.Frame(screen_bezel, bg=ShellStyle.BEZEL)
        screen_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        tk.Canvas(screen_header, width=18, height=18, bg=ShellStyle.BEZEL, highlightthickness=0).pack(side="left", padx=4)
        header_light_left = tk.Canvas(screen_header, width=18, height=18, bg=ShellStyle.BEZEL, highlightthickness=0)
        header_light_left.pack(side="left")
        header_light_left.create_oval(3, 3, 15, 15, fill="#FF5C5C", outline="")
        header_light_right = tk.Canvas(screen_header, width=18, height=18, bg=ShellStyle.BEZEL, highlightthickness=0)
        header_light_right.pack(side="left", padx=(2, 0))
        header_light_right.create_oval(3, 3, 15, 15, fill="#FF5C5C", outline="")

        self.image_panel = tk.Frame(
            screen_bezel,
            bg=ShellStyle.SCREEN_BG,
            width=420,
            height=320,
            highlightbackground="#61790A",
            highlightthickness=2,
        )
        self.image_panel.grid(row=1, column=0, sticky="nsew")
        self.image_panel.grid_propagate(False)

        self.image_canvas = tk.Canvas(
            self.image_panel,
            bg=ShellStyle.SCREEN_BG,
            highlightthickness=0,
            bd=0,
        )
        self.image_canvas.pack(fill="both", expand=True)
        self.image_canvas.bind("<Configure>", self._on_image_panel_resize)

        footer = tk.Frame(screen_bezel, bg=ShellStyle.BEZEL)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(1, weight=1)

        speaker_light = tk.Canvas(footer, width=28, height=28, bg=ShellStyle.BEZEL, highlightthickness=0)
        speaker_light.grid(row=0, column=0, sticky="w")
        speaker_light.create_oval(5, 5, 23, 23, fill="#FF5C5C", outline="")

        footer_spacer = tk.Frame(footer, bg=ShellStyle.BEZEL)
        footer_spacer.grid(row=0, column=1, sticky="ew")

        speaker = tk.Canvas(footer, width=70, height=26, bg=ShellStyle.BEZEL, highlightthickness=0)
        speaker.grid(row=0, column=2, sticky="e")
        for x in range(10, 65, 10):
            speaker.create_line(x, 6, x, 20, fill="#BBBBBB", width=2)

        info_panel = tk.Frame(left, bg=ShellStyle.PANEL_BG, padx=12, pady=12)
        info_panel.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        info_panel.columnconfigure(0, weight=1)

        title_row = tk.Frame(info_panel, bg=ShellStyle.PANEL_BG)
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.columnconfigure(0, weight=1)

        self.name_label = tk.Label(
            title_row,
            textvariable=self.name_var,
            bg=ShellStyle.PANEL_BG,
            fg="#111111",
            font=Fonts.NAME,
            anchor="w",
        )
        self.name_label.grid(row=0, column=0, sticky="ew")

        self.cry_button = tk.Button(
            title_row,
            text="♪ CRY",
            command=self._play_current_cry,
            bg=ShellStyle.BUTTON_BLACK,
            fg="#F4F4F4",
            activebackground="#3A3A3A",
            activeforeground="#FFFFFF",
            relief="flat",
            font=Fonts.CRY_BUTTON,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.cry_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

        tk.Label(
            info_panel,
            textvariable=self.meta_var,
            bg=ShellStyle.PANEL_BG,
            fg="#222222",
            font=Fonts.LABEL,
            anchor="w",
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(6, 4))

        tk.Label(
            info_panel,
            textvariable=self.type_var,
            bg=ShellStyle.PANEL_BG,
            fg="#111111",
            font=Fonts.LABEL_BOLD,
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", pady=(4, 2))

        tk.Label(
            info_panel,
            textvariable=self.ability_var,
            bg=ShellStyle.PANEL_BG,
            fg="#222222",
            font=Fonts.LABEL,
            anchor="w",
            justify="left",
        ).grid(row=3, column=0, sticky="ew")

        lower = tk.Frame(left, bg=ShellStyle.SHELL_RED)
        lower.grid(row=3, column=0, sticky="nsew")
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(0, weight=1, minsize=180)

        entry_box = tk.Frame(lower, bg="#ABB87A", highlightbackground="#5F6F28", highlightthickness=2)
        entry_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        entry_box.columnconfigure(0, weight=1)
        entry_box.rowconfigure(1, weight=1)
        tk.Label(
            entry_box,
            text="DEX ENTRY",
            bg="#ABB87A",
            fg=ShellStyle.SCREEN_TEXT,
            font=Fonts.PANEL_TITLE,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        self.entry_text = tk.Text(
            entry_box,
            wrap="word",
            bg=ShellStyle.SCREEN_BG,
            fg=ShellStyle.SCREEN_TEXT,
            relief="flat",
            insertbackground=ShellStyle.SCREEN_TEXT,
            font=Fonts.SCREEN_TEXT,
            padx=10,
            pady=10,
        )
        self.entry_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.entry_text.config(state="disabled")

        stats_box = tk.Frame(lower, bg="#ABB87A", highlightbackground="#5F6F28", highlightthickness=2)
        stats_box.grid(row=0, column=1, sticky="nsew")
        stats_box.columnconfigure(0, weight=1)
        stats_box.rowconfigure(1, weight=1)
        tk.Label(
            stats_box,
            text="STATS",
            bg="#ABB87A",
            fg=ShellStyle.SCREEN_TEXT,
            font=Fonts.PANEL_TITLE,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        self.stats_text = tk.Text(
            stats_box,
            wrap="word",
            bg=ShellStyle.SCREEN_BG,
            fg=ShellStyle.SCREEN_TEXT,
            relief="flat",
            insertbackground=ShellStyle.SCREEN_TEXT,
            font=Fonts.SCREEN_TEXT,
            padx=10,
            pady=10,
        )
        self.stats_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.stats_text.config(state="disabled")

    def _build_hinge(self, parent: tk.Frame) -> None:
        hinge = tk.Frame(parent, bg=ShellStyle.SHELL_RED_DARK, width=34)
        hinge.grid(row=0, column=1, sticky="ns")
        hinge.grid_propagate(False)
        hinge.columnconfigure(0, weight=1)

        for idx in range(7):
            spacer = tk.Frame(hinge, bg=ShellStyle.SHELL_RED_DARK, height=18)
            spacer.grid(row=idx * 2, column=0, sticky="ew")
            notch = tk.Frame(hinge, bg="#6A1111", height=10)
            notch.grid(row=idx * 2 + 1, column=0, sticky="ew", padx=3)

    def _build_right_half(self, parent: tk.Frame) -> None:
        right = tk.Frame(parent, bg=ShellStyle.SHELL_RED, padx=18, pady=16)
        right.grid(row=0, column=2, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        search_panel = tk.Frame(right, bg=ShellStyle.PANEL_BG, padx=14, pady=14)
        search_panel.grid(row=0, column=0, sticky="ew", pady=(18, 12))
        search_panel.columnconfigure(0, weight=1)

        tk.Label(
            search_panel,
            text="SEARCH BY NAME OR #",
            bg=ShellStyle.PANEL_BG,
            fg="#1A1A1A",
            font=Fonts.LABEL_BOLD,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        self.search_var.trace_add("write", lambda *_: self._filter_list())
        search_entry = tk.Entry(
            search_panel,
            textvariable=self.search_var,
            bg=ShellStyle.SCREEN_BG,
            fg=ShellStyle.SCREEN_TEXT,
            relief="flat",
            insertbackground=ShellStyle.SCREEN_TEXT,
            font=Fonts.SEARCH,
            bd=0,
        )
        search_entry.grid(row=1, column=0, sticky="ew", pady=(10, 0), ipady=10)

        control_row = tk.Frame(right, bg=ShellStyle.SHELL_RED)
        control_row.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        control_row.columnconfigure(2, weight=1)

        prev_btn = tk.Button(
            control_row,
            text="◀ PREV",
            command=self._select_previous,
            bg=ShellStyle.BUTTON_BLACK,
            fg="#F4F4F4",
            activebackground="#3A3A3A",
            activeforeground="#FFFFFF",
            relief="flat",
            font=Fonts.BUTTON,
            padx=14,
            pady=10,
            cursor="hand2",
        )
        prev_btn.grid(row=0, column=0, sticky="w")

        next_btn = tk.Button(
            control_row,
            text="NEXT ▶",
            command=self._select_next,
            bg=ShellStyle.BUTTON_BLACK,
            fg="#F4F4F4",
            activebackground="#3A3A3A",
            activeforeground="#FFFFFF",
            relief="flat",
            font=Fonts.BUTTON,
            padx=14,
            pady=10,
            cursor="hand2",
        )
        next_btn.grid(row=0, column=1, sticky="w", padx=(10, 0))

        list_panel = tk.Frame(right, bg="#ABB87A", highlightbackground="#5F6F28", highlightthickness=2)
        list_panel.grid(row=2, column=0, sticky="nsew")
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(1, weight=1)

        tk.Label(
            list_panel,
            text="KANTO INDEX 001-151",
            bg="#ABB87A",
            fg=ShellStyle.SCREEN_TEXT,
            font=("Courier", 13, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))

        list_inner = tk.Frame(list_panel, bg="#ABB87A")
        list_inner.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        list_inner.columnconfigure(0, weight=1)
        list_inner.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_inner,
            activestyle="none",
            exportselection=False,
            bg=ShellStyle.SCREEN_BG,
            fg=ShellStyle.SCREEN_TEXT,
            selectbackground="#6F8D0D",
            selectforeground="#F8F8F8",
            relief="flat",
            borderwidth=0,
            font=Fonts.LIST,
            width=22,
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        scrollbar = tk.Scrollbar(list_inner, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)

        bottom_controls = tk.Frame(right, bg=ShellStyle.SHELL_RED)
        bottom_controls.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        bottom_controls.columnconfigure(1, weight=1)

        small_buttons = tk.Frame(bottom_controls, bg=ShellStyle.SHELL_RED)
        small_buttons.grid(row=0, column=0, sticky="w")
        tk.Canvas(small_buttons, width=56, height=18, bg=ShellStyle.SHELL_RED, highlightthickness=0).pack(side="left", padx=(0, 10))
        btn_red = tk.Canvas(small_buttons, width=56, height=18, bg=ShellStyle.SHELL_RED, highlightthickness=0)
        btn_red.pack(side="left", padx=(0, 10))
        btn_red.create_oval(2, 2, 54, 16, fill="#E53935", outline="#8E1C1C", width=2)
        btn_blue = tk.Canvas(small_buttons, width=56, height=18, bg=ShellStyle.SHELL_RED, highlightthickness=0)
        btn_blue.pack(side="left")
        btn_blue.create_oval(2, 2, 54, 16, fill="#1E88E5", outline="#0D47A1", width=2)

        dpad = tk.Canvas(bottom_controls, width=120, height=110, bg=ShellStyle.SHELL_RED, highlightthickness=0)
        dpad.grid(row=0, column=2, sticky="e")
        self._draw_dpad(dpad)

        tk.Label(
            right,
            textvariable=self.status_var,
            bg=ShellStyle.SHELL_RED,
            fg="#FFF4E8",
            font=Fonts.LABEL,
            anchor="w",
            justify="left",
        ).grid(row=4, column=0, sticky="ew", pady=(10, 0))

    def _draw_dpad(self, canvas: tk.Canvas) -> None:
        fill = ShellStyle.BUTTON_BLACK
        outline = "#111111"
        canvas.create_rectangle(46, 12, 74, 98, fill=fill, outline=outline, width=3)
        canvas.create_rectangle(18, 40, 102, 68, fill=fill, outline=outline, width=3)
        canvas.create_oval(51, 45, 69, 63, fill="#444444", outline="")

    def _set_idle_content(self) -> None:
        set_readonly_text(self.entry_text, "Select a Pokémon to load its Pokédex entry.")
        set_readonly_text(self.stats_text, "HP\nAttack\nDefense\nSpecial Attack\nSpecial Defense\nSpeed")
        self._render_no_image("NO SIGNAL")

    def _load_pokemon_list(self) -> None:
        def worker() -> None:
            try:
                pokemon = get_original_151()
                self.root.after(0, lambda: self._finish_loading_list(pokemon))
            except Exception as exc:
                self.root.after(0, lambda: self._set_error(f"Could not load Pokémon list: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_loading_list(self, pokemon: List[Dict[str, Any]]) -> None:
        self.all_pokemon = pokemon
        self.filtered_pokemon = pokemon[:]
        self._refresh_listbox()
        self.status_var.set(f"Kanto registry online. Loaded {len(pokemon)} Pokémon.")

        if pokemon:
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.listbox.see(0)
            self.root.after_idle(self._on_select)

    def _filter_list(self) -> None:
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_pokemon = self.all_pokemon[:]
        else:
            self.filtered_pokemon = [
                pokemon
                for pokemon in self.all_pokemon
                if query in pokemon["name"].lower() or query in str(pokemon["id"])
            ]

        self._refresh_listbox()
        if self.filtered_pokemon:
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.listbox.see(0)
            self.root.after_idle(self._on_select)
        else:
            self.status_var.set("No Pokémon match that scan.")
            self.current_details = None
            self.current_image_data = None
            self.current_photo = None
            self.name_var.set("NO MATCH")
            self.meta_var.set("Try another search term.")
            self.type_var.set("Types: --")
            self.ability_var.set("Abilities: --")
            self._render_no_image("NO IMAGE")
            set_readonly_text(self.entry_text, "Select a Pokémon to load its Pokédex entry.")
            set_readonly_text(self.stats_text, "HP\nAttack\nDefense\nSpecial Attack\nSpecial Defense\nSpeed")

    def _refresh_listbox(self) -> None:
        self.listbox.delete(0, tk.END)
        for pokemon in self.filtered_pokemon:
            self.listbox.insert(tk.END, f"#{pokemon['id']:03}  {pokemon['name']}")

    def _select_previous(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        new_index = max(0, selection[0] - 1)
        self._select_listbox_index(new_index)

    def _select_next(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        new_index = min(len(self.filtered_pokemon) - 1, selection[0] + 1)
        self._select_listbox_index(new_index)

    def _select_listbox_index(self, index: int) -> None:
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)
        self.listbox.event_generate("<<ListboxSelect>>")

    def _on_select(self, _event: object = None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index >= len(self.filtered_pokemon):
            return

        pokemon = self.filtered_pokemon[index]
        self.status_var.set(f"Scanning #{pokemon['id']:03} {pokemon['name']}...")

        def worker() -> None:
            try:
                details = get_pokemon_details(pokemon["id"])
                image_data = None
                if details.get("image_url"):
                    try:
                        image_data = get_image_bytes(details["image_url"])
                    except PokeAPIError:
                        image_data = None
                self.root.after(0, lambda: self._display_pokemon(details, image_data))
            except Exception as exc:
                self.root.after(0, lambda: self._set_error(f"Could not load details: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _display_pokemon(self, details: Dict[str, Any], image_data: Optional[bytes]) -> None:
        self.current_details = details
        self.current_image_data = image_data
        self.name_var.set(f"#{details['id']:03} {details['name']}")
        self.meta_var.set(
            f"{details['genus']}   |   HT {details['height_m']:.1f} m   |   WT {details['weight_kg']:.1f} kg"
        )
        self.type_var.set("Types: " + ", ".join(details["types"]))
        self.ability_var.set("Abilities: " + ", ".join(details["abilities"]))

        set_readonly_text(self.entry_text, details["flavor_text"])
        stats_order = ["Hp", "Attack", "Defense", "Special Attack", "Special Defense", "Speed"]
        stats_lines = [f"{name:<16} {details['stats'].get(name, '--')}" for name in stats_order]
        set_readonly_text(self.stats_text, "\n".join(stats_lines))

        self._render_current_image()
        self.status_var.set(f"Entry ready for #{details['id']:03} {details['name']}.")

    def _on_image_panel_resize(self, _event: tk.Event) -> None:
        if self.current_image_data:
            self._render_current_image()
        else:
            self._render_no_image("NO SIGNAL")

    def _render_current_image(self) -> None:
        if not self.current_image_data:
            self._render_no_image("NO IMAGE")
            return

        width = max(self.image_canvas.winfo_width(), 360)
        height = max(self.image_canvas.winfo_height(), 220)
        target_width = max(96, width - 24)
        target_height = max(96, height - 24)

        try:
            self.current_photo = image_bytes_to_photoimage(
                self.current_image_data,
                max_width=target_width,
                max_height=target_height,
            )
            self.image_canvas.delete("all")
            
            x = width // 2
            y = height // 2 - 25 
            self.image_canvas.create_image(x, y, image=self.current_photo, anchor="center")
        except tk.TclError:
            self.current_photo = None
            self._render_no_image("SPRITE ERROR")

    def _render_no_image(self, message: str) -> None:
        width = max(self.image_canvas.winfo_width(), 280)
        height = max(self.image_canvas.winfo_height(), 180)
        self.image_canvas.delete("all")
        self.image_canvas.create_text(
            width // 2,
            height // 2,
            text=message,
            fill=ShellStyle.SCREEN_TEXT,
            font=Fonts.SCREEN_TEXT_LARGE,
            justify="center",
        )

    def _play_current_cry(self) -> None:
        if not self.current_details:
            self.status_var.set("Pick a Pokémon first before playing a cry.")
            return

        cry_url = self.current_details.get("cry_url")
        if not cry_url:
            self.status_var.set("No cry is available for this Pokémon.")
            return

        pokemon_id = self.current_details["id"]
        pokemon_name = self.current_details["name"]
        self.status_var.set(f"Opening cry for #{pokemon_id:03} {pokemon_name}...")

        def worker() -> None:
            try:
                cry_path = play_pokemon_cry(cry_url, pokemon_id, pokemon_name)
                self.root.after(
                    0,
                    lambda: self.status_var.set(f"Cry opened in your system audio app: {cry_path.name}"),
                )
            except CryPlaybackError as exc:
                self.root.after(0, lambda: self.status_var.set(f"Cry error: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _set_error(self, message: str) -> None:
        self.current_details = None
        self.current_image_data = None
        self.current_photo = None
        self.status_var.set(message)
        self.name_var.set("SYSTEM ERROR")
        self.meta_var.set("")
        self.type_var.set("Types: --")
        self.ability_var.set("Abilities: --")
        self._render_no_image("NO SIGNAL")
        set_readonly_text(self.entry_text, message)
        set_readonly_text(self.stats_text, "")



def main() -> None:
    root = tk.Tk()
    PokedexApp(root)
    root.mainloop()
