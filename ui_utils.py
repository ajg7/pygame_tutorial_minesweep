import base64
import io
import tkinter as tk

try:
    from PIL import Image, ImageTk  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover - optional dependency fallback
    Image = None
    ImageTk = None


def set_readonly_text(widget: tk.Text, content: str) -> None:
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", content)
    widget.config(state="disabled")



def image_bytes_to_photoimage(image_data: bytes, max_width: int, max_height: int):
    """Return a pixel-crisp image scaled to fit inside the given box."""
    safe_max_width = max(1, int(max_width))
    safe_max_height = max(1, int(max_height))

    if Image is not None and ImageTk is not None:
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        width, height = image.size
        scale = max(1, min(safe_max_width // width, safe_max_height // height))
        resized = image.resize((width * scale, height * scale), Image.Resampling.NEAREST)
        return ImageTk.PhotoImage(resized)

    encoded = base64.b64encode(image_data).decode("ascii")
    photo = tk.PhotoImage(data=encoded, format="png")
    scale = max(1, min(safe_max_width // photo.width(), safe_max_height // photo.height()))
    return photo.zoom(scale, scale)
