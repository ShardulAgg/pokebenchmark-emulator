"""Tests for GBAEmulator and frame capture utilities."""
import io
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image


def make_emulator():
    """Create a GBAEmulator with a mocked gba instance, avoiding ROM loading."""
    from pokebenchmark_emulator.gba import GBAEmulator

    emu = GBAEmulator.__new__(GBAEmulator)

    mock_core = MagicMock()
    mock_core.desired_video_dimensions.return_value = (240, 160)
    mock_core.save_raw_state.return_value = b"\x00" * 128
    mock_core.run_frame.return_value = None

    mock_gba = MagicMock()
    mock_gba.core = mock_core

    emu.gba = mock_gba

    # Set up framebuffer manually (bypass _setup_framebuffer)
    mock_fb = MagicMock()
    mock_fb.to_pil.return_value = Image.new("RGB", (240, 160), color=(0, 0, 0))
    emu._framebuffer = mock_fb

    return emu


class TestValidButtons:
    def test_valid_buttons_count(self):
        from pokebenchmark_emulator.gba import GBAEmulator
        assert len(GBAEmulator.VALID_BUTTONS) == 10

    def test_valid_buttons_contents(self):
        from pokebenchmark_emulator.gba import GBAEmulator
        expected = {"up", "down", "left", "right", "A", "B", "L", "R", "start", "select"}
        assert set(GBAEmulator.VALID_BUTTONS) == expected


class TestPressButton:
    def test_press_button_raises_for_invalid(self):
        from pokebenchmark_emulator.gba import GBAEmulator
        emu = make_emulator()
        with pytest.raises(ValueError, match="Invalid button: X"):
            emu.press_button("X")

    def test_press_button_calls_press_key(self):
        emu = make_emulator()
        emu.press_button("A", frames=3)
        emu.gba.press_key.assert_called_once_with("A", frames=3)

    def test_press_button_default_frames(self):
        emu = make_emulator()
        emu.press_button("start")
        emu.gba.press_key.assert_called_once_with("start", frames=2)


class TestPressButtons:
    def test_press_buttons_calls_press_key_for_each(self):
        emu = make_emulator()
        emu.press_buttons(["A", "B", "start"])
        assert emu.gba.press_key.call_count == 3

    def test_press_buttons_passes_wait_frames(self):
        emu = make_emulator()
        emu.press_buttons(["up", "down"], wait_frames=5)
        calls = emu.gba.press_key.call_args_list
        for call in calls:
            assert call.kwargs["frames"] == 5

    def test_press_buttons_empty_list(self):
        emu = make_emulator()
        emu.press_buttons([])
        emu.gba.press_key.assert_not_called()


class TestWait:
    def test_wait_calls_gba_wait(self):
        emu = make_emulator()
        emu.wait(10)
        emu.gba.wait.assert_called_once_with(10)


class TestReadMemory:
    def test_read_u32_calls_gba_read_u32(self):
        emu = make_emulator()
        emu.gba.read_u32.return_value = 0xDEADBEEF
        result = emu.read_u32(0x02000000)
        emu.gba.read_u32.assert_called_once_with(0x02000000)
        assert result == 0xDEADBEEF

    def test_read_u16_calls_gba_read_u16(self):
        emu = make_emulator()
        emu.gba.read_u16.return_value = 0x1234
        result = emu.read_u16(0x02000000)
        emu.gba.read_u16.assert_called_once_with(0x02000000)
        assert result == 0x1234

    def test_read_u8_calls_gba_read_u8(self):
        emu = make_emulator()
        emu.gba.read_u8.return_value = 0x42
        result = emu.read_u8(0x02000000)
        emu.gba.read_u8.assert_called_once_with(0x02000000)
        assert result == 0x42


class TestSaveLoadState:
    def test_save_state_uses_core(self):
        emu = make_emulator()
        state = emu.save_state()
        emu.gba.core.save_raw_state.assert_called_once()
        assert state == b"\x00" * 128

    def test_load_state_uses_core(self):
        emu = make_emulator()
        data = b"\xff" * 64
        emu.load_state(data)
        emu.gba.core.load_raw_state.assert_called_once_with(data)
        emu.gba.core.run_frame.assert_called_once()

    def test_save_state_to_file(self, tmp_path):
        emu = make_emulator()
        state_file = tmp_path / "state.bin"
        emu.gba.core.save_raw_state.return_value = b"\xab\xcd"
        emu.save_state_to_file(str(state_file))
        assert state_file.read_bytes() == b"\xab\xcd"

    def test_load_state_from_file(self, tmp_path):
        emu = make_emulator()
        state_file = tmp_path / "state.bin"
        state_file.write_bytes(b"\x01\x02\x03")
        emu.load_state_from_file(str(state_file))
        emu.gba.core.load_raw_state.assert_called_once_with(b"\x01\x02\x03")


class TestCaptureFrame:
    def test_capture_frame_returns_image_and_bytes(self):
        from pokebenchmark_emulator.frame import capture_frame
        emu = make_emulator()
        img, png_bytes = capture_frame(emu)
        assert isinstance(img, Image.Image)
        assert isinstance(png_bytes, bytes)
        # Verify it's valid PNG
        assert png_bytes[:4] == b"\x89PNG"

    def test_capture_frame_runs_frame(self):
        from pokebenchmark_emulator.frame import capture_frame
        emu = make_emulator()
        capture_frame(emu)
        emu.gba.core.run_frame.assert_called()
