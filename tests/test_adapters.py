"""Tests for game adapters (base, emerald, firered). All mocked — no ROM needed."""
import inspect
from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# 1. GameState has required fields
# ---------------------------------------------------------------------------

class TestGameStateFields:
    def test_game_state_has_required_fields(self):
        from pokebenchmark_emulator.adapters.base import GameState, BattleState
        gs = GameState(
            player_name="RED",
            location="Pallet Town",
            x=5,
            y=10,
            facing="up",
            badges=[],
            money=3000,
            party=[],
            bag=[],
            dialog="",
            in_battle=False,
        )
        assert gs.player_name == "RED"
        assert gs.location == "Pallet Town"
        assert gs.x == 5
        assert gs.y == 10
        assert gs.facing == "up"
        assert gs.badges == []
        assert gs.money == 3000
        assert gs.party == []
        assert gs.bag == []
        assert gs.dialog == ""
        assert gs.in_battle is False
        assert gs.battle_state is None

    def test_battle_state_has_required_fields(self):
        from pokebenchmark_emulator.adapters.base import BattleState
        bs = BattleState(
            is_wild=True,
            enemy_species="Pidgey",
            enemy_level=5,
            enemy_hp=20,
            enemy_max_hp=20,
        )
        assert bs.is_wild is True
        assert bs.enemy_species == "Pidgey"
        assert bs.enemy_level == 5
        assert bs.enemy_hp == 20
        assert bs.enemy_max_hp == 20
        assert bs.enemy_types == []

    def test_game_state_accepts_battle_state(self):
        from pokebenchmark_emulator.adapters.base import GameState, BattleState
        bs = BattleState(
            is_wild=True,
            enemy_species="Rattata",
            enemy_level=3,
            enemy_hp=15,
            enemy_max_hp=15,
        )
        gs = GameState(
            player_name="ASH",
            location="Route 1",
            x=0,
            y=0,
            facing="down",
            badges=[],
            money=500,
            party=[],
            bag=[],
            dialog="",
            in_battle=True,
            battle_state=bs,
        )
        assert gs.battle_state is bs


# ---------------------------------------------------------------------------
# 2. GameState.to_text includes key info
# ---------------------------------------------------------------------------

class TestGameStateToText:
    def _make_state(self, **kwargs):
        from pokebenchmark_emulator.adapters.base import GameState
        defaults = dict(
            player_name="RED",
            location="Cerulean City",
            x=12,
            y=8,
            facing="left",
            badges=["Boulder"],
            money=1500,
            party=[{"species": "Charmander", "level": 10, "hp": 35, "max_hp": 35, "moves": ["Scratch", "Growl"]}],
            bag=[{"item": "Potion", "quantity": 3}],
            dialog="",
            in_battle=False,
        )
        defaults.update(kwargs)
        return GameState(**defaults)

    def test_to_text_contains_player_name(self):
        gs = self._make_state()
        assert "RED" in gs.to_text()

    def test_to_text_contains_location(self):
        gs = self._make_state()
        text = gs.to_text()
        assert "Cerulean City" in text

    def test_to_text_contains_coordinates(self):
        gs = self._make_state()
        text = gs.to_text()
        assert "12" in text
        assert "8" in text

    def test_to_text_contains_facing(self):
        gs = self._make_state()
        assert "left" in gs.to_text()

    def test_to_text_contains_money(self):
        gs = self._make_state()
        assert "1500" in gs.to_text()

    def test_to_text_contains_badges(self):
        gs = self._make_state()
        assert "Boulder" in gs.to_text()

    def test_to_text_no_badges(self):
        gs = self._make_state(badges=[])
        assert "none" in gs.to_text()

    def test_to_text_contains_party_species(self):
        gs = self._make_state()
        assert "Charmander" in gs.to_text()

    def test_to_text_contains_party_level(self):
        gs = self._make_state()
        assert "10" in gs.to_text()

    def test_to_text_contains_party_hp(self):
        gs = self._make_state()
        assert "35/35" in gs.to_text()

    def test_to_text_contains_party_moves(self):
        gs = self._make_state()
        text = gs.to_text()
        assert "Scratch" in text
        assert "Growl" in text

    def test_to_text_empty_party(self):
        gs = self._make_state(party=[])
        assert "empty" in gs.to_text()

    def test_to_text_contains_bag_item(self):
        gs = self._make_state()
        text = gs.to_text()
        assert "Potion" in text
        assert "3" in text

    def test_to_text_empty_bag(self):
        gs = self._make_state(bag=[])
        assert "empty" in gs.to_text()

    def test_to_text_contains_dialog(self):
        gs = self._make_state(dialog="Hello there!")
        assert "Hello there!" in gs.to_text()

    def test_to_text_no_dialog_when_empty(self):
        gs = self._make_state(dialog="")
        assert "Dialog" not in gs.to_text()

    def test_to_text_contains_battle_info(self):
        from pokebenchmark_emulator.adapters.base import BattleState
        bs = BattleState(
            is_wild=True,
            enemy_species="Pidgey",
            enemy_level=4,
            enemy_hp=18,
            enemy_max_hp=18,
        )
        gs = self._make_state(in_battle=True, battle_state=bs)
        text = gs.to_text()
        assert "Pidgey" in text
        assert "Wild" in text
        assert "18/18" in text

    def test_to_text_trainer_battle(self):
        from pokebenchmark_emulator.adapters.base import BattleState
        bs = BattleState(
            is_wild=False,
            enemy_species="Squirtle",
            enemy_level=8,
            enemy_hp=30,
            enemy_max_hp=30,
        )
        gs = self._make_state(in_battle=True, battle_state=bs)
        assert "Trainer" in gs.to_text()

    def test_to_text_no_battle_section_when_not_in_battle(self):
        gs = self._make_state(in_battle=False)
        assert "Battle" not in gs.to_text()


# ---------------------------------------------------------------------------
# 3. GameAdapter is abstract
# ---------------------------------------------------------------------------

class TestGameAdapterAbstract:
    def test_game_adapter_is_abstract(self):
        from pokebenchmark_emulator.adapters.base import GameAdapter
        assert inspect.isabstract(GameAdapter)

    def test_cannot_instantiate_game_adapter(self):
        from pokebenchmark_emulator.adapters.base import GameAdapter
        with pytest.raises(TypeError):
            GameAdapter()

    def test_game_adapter_requires_game_name(self):
        from pokebenchmark_emulator.adapters.base import GameAdapter
        assert "game_name" in GameAdapter.__abstractmethods__

    def test_game_adapter_requires_read_state(self):
        from pokebenchmark_emulator.adapters.base import GameAdapter
        assert "read_state" in GameAdapter.__abstractmethods__


# ---------------------------------------------------------------------------
# 4-6. EmeraldAdapter
# ---------------------------------------------------------------------------

def _make_mock_pygba_state():
    """Build a mock state dict matching the real pygba get_game_state output structure."""
    return {
        "pos": {"x": 7, "y": 12},
        "location": {"mapGroup": 0, "mapNum": 1, "warpId": 0, "x": 0, "y": 0},
        "badges": [True, False, False, False, False, False, False, False],
        "money": 2500,
        "party": [
            {
                "level": 7,
                "hp": 28,
                "maxHp": 28,
                "box": {
                    "nickname": "MUDKIP",
                    "substructs": (
                        {"species": 258, "heldItem": 0, "experience": 100, "ppBonuses": 0, "friendship": 70},
                        {"moves": [33, 45, 0, 0], "pp": [35, 20, 0, 0]},
                        {},
                        {},
                    ),
                },
            }
        ],
    }


def _make_mock_save_block_2():
    """Build a mock save_block_2 dict matching pygba's read_save_block_2 output."""
    return {
        "playerName": "BRENDAN",
        "playerGender": 0,
        "encryptionKey": 0,
    }


class TestEmeraldAdapter:
    def test_is_game_adapter(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter
        from pokebenchmark_emulator.adapters.base import GameAdapter
        assert issubclass(EmeraldAdapter, GameAdapter)

    def test_game_name(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter
        adapter = EmeraldAdapter()
        assert adapter.game_name == "emerald"

    def test_read_state_returns_game_state(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter
        from pokebenchmark_emulator.adapters.base import GameState

        mock_emulator = MagicMock()
        mock_emulator.gba = MagicMock()

        adapter = EmeraldAdapter()
        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert isinstance(result, GameState)

    def test_read_state_calls_get_game_state_with_gba(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()) as mock_get, \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            adapter.read_state(mock_emulator)
            mock_get.assert_called_once_with(mock_emulator.gba)

    def test_read_state_player_name(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert result.player_name == "BRENDAN"

    def test_read_state_coordinates(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert result.x == 7
        assert result.y == 12

    def test_read_state_money(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert result.money == 2500

    def test_read_state_badges(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert "Stone" in result.badges
        assert len(result.badges) == 1  # Only first badge is True

    def test_read_state_party(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert len(result.party) == 1
        mon = result.party[0]
        assert mon["level"] == 7
        assert mon["hp"] == 28
        assert mon["max_hp"] == 28

    def test_read_state_no_battle(self):
        from pokebenchmark_emulator.adapters.emerald import EmeraldAdapter

        mock_emulator = MagicMock()
        adapter = EmeraldAdapter()

        with patch("pokebenchmark.adapters.emerald.get_game_state", return_value=_make_mock_pygba_state()), \
             patch("pokebenchmark.adapters.emerald.read_save_block_2", return_value=_make_mock_save_block_2()):
            result = adapter.read_state(mock_emulator)

        assert result.in_battle is False
        assert result.battle_state is None


# ---------------------------------------------------------------------------
# 7-9. FireRedAdapter
# ---------------------------------------------------------------------------

class TestFireRedAdapter:
    def test_is_game_adapter(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter
        from pokebenchmark_emulator.adapters.base import GameAdapter
        assert issubclass(FireRedAdapter, GameAdapter)

    def test_game_name(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter
        adapter = FireRedAdapter()
        assert adapter.game_name == "firered"

    def _make_mock_emulator(self):
        """Build a mock emulator that simulates FireRed memory layout."""
        # SAVEBLOCK2_PTR = 0x0300500C → points to 0x02024000
        # SAVEBLOCK1_PTR = 0x03005008 → points to 0x02025000
        SAVEBLOCK1_BASE = 0x02025000
        SAVEBLOCK2_BASE = 0x02024000

        mock_emu = MagicMock()

        def read_u32(addr):
            if addr == 0x03005008:
                return SAVEBLOCK1_BASE
            if addr == 0x0300500C:
                return SAVEBLOCK2_BASE
            return 0

        def read_u16(addr):
            # x at saveblock1 + 0x0
            if addr == SAVEBLOCK1_BASE + 0x0:
                return 5
            # y at saveblock1 + 0x2
            if addr == SAVEBLOCK1_BASE + 0x2:
                return 10
            return 0

        def read_u8(addr):
            # mapGroup at saveblock1 + 0x4
            if addr == SAVEBLOCK1_BASE + 0x4:
                return 3
            # mapNum at saveblock1 + 0x5
            if addr == SAVEBLOCK1_BASE + 0x5:
                return 1
            # badges at saveblock2 + 0x08 (Boulder + Cascade = bits 0 and 1)
            if addr == SAVEBLOCK2_BASE + 0x08:
                return 0b00000011
            return 0

        # Player name at saveblock2 + 0x0 — "RED" in Gen3 charmap
        # Gen3: R=0xCC, E=0xBF, D=0xBE, terminator=0xFF
        def read_memory(addr, size):
            if addr == SAVEBLOCK2_BASE + 0x0:
                return bytes([0xCC, 0xBF, 0xBE, 0xFF, 0xFF, 0xFF, 0xFF])[:size]
            return bytes(size)

        mock_emu.read_u32.side_effect = read_u32
        mock_emu.read_u16.side_effect = read_u16
        mock_emu.read_u8.side_effect = read_u8
        mock_emu.read_memory.side_effect = read_memory
        return mock_emu

    def test_read_state_returns_game_state(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter
        from pokebenchmark_emulator.adapters.base import GameState

        adapter = FireRedAdapter()
        mock_emu = self._make_mock_emulator()
        result = adapter.read_state(mock_emu)

        assert isinstance(result, GameState)

    def test_read_state_player_name(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_mock_emulator()
        result = adapter.read_state(mock_emu)

        assert result.player_name == "RED"

    def test_read_state_coordinates(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_mock_emulator()
        result = adapter.read_state(mock_emu)

        assert result.x == 5
        assert result.y == 10

    def test_read_state_badges(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_mock_emulator()
        result = adapter.read_state(mock_emu)

        assert "Boulder" in result.badges
        assert "Cascade" in result.badges
        assert len(result.badges) == 2

    def test_decode_string_basic(self):
        from pokebenchmark_emulator.adapters.firered import decode_string, FIRERED_CHARMAP

        # Find byte codes for R, E, D via reverse lookup
        inv = {v: k for k, v in FIRERED_CHARMAP.items()}
        if "R" in inv and "E" in inv and "D" in inv:
            data = bytes([inv["R"], inv["E"], inv["D"], 0xFF])
            assert decode_string(data) == "RED"

    def test_decode_string_terminates_at_ff(self):
        from pokebenchmark_emulator.adapters.firered import decode_string, FIRERED_CHARMAP

        inv = {v: k for k, v in FIRERED_CHARMAP.items()}
        if "A" in inv:
            # "A" followed by terminator and then more data
            data = bytes([inv["A"], 0xFF, inv.get("B", 0xFF), inv.get("C", 0xFF)])
            result = decode_string(data)
            assert result == "A"

    def test_firered_charmap_exists(self):
        from pokebenchmark_emulator.adapters.firered import FIRERED_CHARMAP
        assert isinstance(FIRERED_CHARMAP, dict)
        assert len(FIRERED_CHARMAP) > 0
        # Check standard letters exist in values
        values = set(FIRERED_CHARMAP.values())
        assert "A" in values
        assert "Z" in values

    def test_firered_charmap_has_lowercase(self):
        from pokebenchmark_emulator.adapters.firered import FIRERED_CHARMAP
        values = set(FIRERED_CHARMAP.values())
        assert "a" in values
        assert "z" in values

    def test_firered_charmap_terminates_at_0xff(self):
        from pokebenchmark_emulator.adapters.firered import decode_string
        # All zeros should give empty or unknown chars, 0xFF terminates
        data = bytes([0xFF])
        result = decode_string(data)
        assert result == ""
