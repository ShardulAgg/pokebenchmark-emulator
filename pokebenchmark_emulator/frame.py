import io
from PIL import Image


def capture_frame(emulator) -> tuple[Image.Image, bytes]:
    img = emulator.screenshot()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()
    return img, png_bytes
