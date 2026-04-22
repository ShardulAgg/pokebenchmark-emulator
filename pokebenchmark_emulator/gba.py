import mgba.log
from pygba import PyGBA

mgba.log.silence()


class GBAEmulator:
    VALID_BUTTONS = ["up", "down", "left", "right", "A", "B", "L", "R", "start", "select"]

    def __init__(self, rom_path: str, save_file: str | None = None):
        self.gba = PyGBA.load(rom_path, autoload_save=(save_file is not None))
        self._setup_framebuffer()

    def _setup_framebuffer(self):
        import mgba.image
        self._framebuffer = mgba.image.Image(*self.gba.core.desired_video_dimensions())
        self.gba.core.set_video_buffer(self._framebuffer)
        self.gba.core.reset()  # must reset after setting video buffer

    def press_button(self, button: str, frames: int = 2):
        if button not in self.VALID_BUTTONS:
            raise ValueError(f"Invalid button: {button}. Must be one of {self.VALID_BUTTONS}")
        self.gba.press_key(button, frames=frames)

    def press_buttons(self, buttons: list[str], wait_frames: int = 2):
        for button in buttons:
            self.press_button(button, frames=wait_frames)

    def wait(self, frames: int):
        self.gba.wait(frames)

    def read_memory(self, address: int, size: int = 1) -> bytes:
        return self.gba.read_memory(address, size)

    def read_u8(self, address: int) -> int:
        return self.gba.read_u8(address)

    def read_u16(self, address: int) -> int:
        return self.gba.read_u16(address)

    def read_u32(self, address: int) -> int:
        return self.gba.read_u32(address)

    def save_state(self) -> bytes:
        raw = self.gba.core.save_raw_state()
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        # cffi buffer from real mgba bindings
        from mgba._pylib import ffi
        return bytes(ffi.buffer(raw))

    def load_state(self, state: bytes):
        self.gba.core.load_raw_state(state)
        self.gba.core.run_frame()

    def save_state_to_file(self, path: str):
        state = self.save_state()
        with open(path, "wb") as f:
            f.write(state)

    def load_state_from_file(self, path: str):
        with open(path, "rb") as f:
            state = f.read()
        self.load_state(state)

    def screenshot(self):
        self.gba.core.run_frame()
        return self._framebuffer.to_pil().convert("RGB")

    def set_keys(self, keys: int) -> None:
        """Set the held-key bitmask (mGBA GBA_KEY_* bits). Persists across frames."""
        self.gba.core.set_keys(keys)

    def run_frame(self) -> None:
        """Advance exactly one frame using currently held keys."""
        self.gba.core.run_frame()

    def framebuffer_image(self):
        """Return the current framebuffer as a PIL RGB image without advancing."""
        return self._framebuffer.to_pil().convert("RGB")

    def reset(self):
        self.gba.core.reset()
