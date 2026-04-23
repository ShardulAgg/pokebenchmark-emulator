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


# ---------------------------------------------------------------------------
# 10. FireRed Gen 3 party extraction
# ---------------------------------------------------------------------------

import struct


def _build_substructs_plaintext(
    species: int,
    held_item: int,
    experience: int,
    pp_bonuses: int,
    friendship: int,
    moves: list[int],
    pps: list[int],
    evs: list[int],
    pokerus: int,
    met_location: int,
    origin: int,
    iv: int,
    ribbons: int,
) -> dict[str, bytes]:
    """Serialize a set of substruct fields into the 4 x 12-byte blocks,
    keyed by 'G'/'A'/'E'/'M'. Exactly matches the on-disk layout expected
    by `_gen3_mon.decrypt_substructs`."""
    g = bytearray(12)
    struct.pack_into("<H", g, 0, species)
    struct.pack_into("<H", g, 2, held_item)
    struct.pack_into("<I", g, 4, experience)
    g[8] = pp_bonuses
    g[9] = friendship
    # bytes 10-11 padding

    a = bytearray(12)
    for i, m in enumerate(moves):
        struct.pack_into("<H", a, i * 2, m)
    for i, p in enumerate(pps):
        a[8 + i] = p

    e = bytearray(12)
    for i, v in enumerate(evs):
        e[i] = v
    # bytes 6..10 condition, 11 padding — leave 0

    m_block = bytearray(12)
    m_block[0] = pokerus
    m_block[1] = met_location
    struct.pack_into("<H", m_block, 2, origin)
    struct.pack_into("<I", m_block, 4, iv)
    struct.pack_into("<I", m_block, 8, ribbons)

    return {"G": bytes(g), "A": bytes(a), "E": bytes(e), "M": bytes(m_block)}


def _encrypt_substruct_block(
    substructs: dict[str, bytes], personality: int, ot_id: int
) -> tuple[bytes, int]:
    """Build the full on-disk 48-byte encrypted block from the 4 plaintext
    substructs. Returns (encrypted_bytes, checksum)."""
    from pokebenchmark_emulator.adapters._gen3_mon import SUBSTRUCT_ORDER

    perm = SUBSTRUCT_ORDER[personality % 24]
    plaintext = bytearray(48)
    for block_index, name in enumerate(perm):
        plaintext[block_index * 12 : (block_index + 1) * 12] = substructs[name]

    # Checksum is sum of 24 u16s of the plaintext block, masked to u16.
    checksum = 0
    for i in range(24):
        checksum = (checksum + struct.unpack_from("<H", plaintext, i * 2)[0]) & 0xFFFF

    key = (personality ^ ot_id) & 0xFFFFFFFF
    encrypted = bytearray(48)
    for i in range(12):
        pt = struct.unpack_from("<I", plaintext, i * 4)[0]
        struct.pack_into("<I", encrypted, i * 4, (pt ^ key) & 0xFFFFFFFF)

    return bytes(encrypted), checksum


def _build_party_mon_struct(
    personality: int,
    ot_id: int,
    nickname_bytes: bytes,
    level: int,
    hp: int,
    max_hp: int,
    status_u32: int,
    substructs: dict[str, bytes],
) -> bytes:
    """Assemble a full 100-byte party PokemonStruct for tests."""
    raw = bytearray(100)
    struct.pack_into("<I", raw, 0x00, personality)
    struct.pack_into("<I", raw, 0x04, ot_id)
    # nickname: 10 bytes, padded with 0xFF terminator
    nick = nickname_bytes[:10].ljust(10, b"\xff")
    raw[0x08:0x12] = nick
    raw[0x12] = 0x02  # language = English
    raw[0x13] = 0x00  # flags
    raw[0x14:0x1B] = b"\xff" * 7  # OT name terminator padding
    raw[0x1B] = 0  # markings
    # checksum + encrypted block
    encrypted, checksum = _encrypt_substruct_block(substructs, personality, ot_id)
    struct.pack_into("<H", raw, 0x1C, checksum)
    struct.pack_into("<H", raw, 0x1E, 0)
    raw[0x20:0x50] = encrypted
    struct.pack_into("<I", raw, 0x50, status_u32)
    raw[0x54] = level
    raw[0x55] = 0  # mail id / pokerus
    struct.pack_into("<H", raw, 0x56, hp)
    struct.pack_into("<H", raw, 0x58, max_hp)
    return bytes(raw)


class TestFireRedPartyExtraction:
    """Unit + integration tests for the Gen 3 party decoder.

    Splits into:
      - `decrypt_substructs` round-trip + checksum-mismatch behavior
      - `species_name` / `move_name` fallbacks
      - `decode_status` enum
      - End-to-end: FireRedAdapter.read_state populates party correctly
    """

    def test_decrypt_substructs_round_trip(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decrypt_substructs

        personality = 0xDEADBEEF
        ot_id = 0x12345678
        substructs = _build_substructs_plaintext(
            species=7,  # Squirtle
            held_item=0,
            experience=1000,
            pp_bonuses=0,
            friendship=70,
            moves=[33, 39, 145, 0],  # Tackle, Tail Whip, Bubble, ---
            pps=[35, 30, 30, 0],
            evs=[1, 2, 3, 4, 5, 6],
            pokerus=0,
            met_location=1,
            origin=0,
            iv=0,
            ribbons=0,
        )
        encrypted, _ = _encrypt_substruct_block(substructs, personality, ot_id)
        out = decrypt_substructs(encrypted, personality, ot_id)
        assert out is not None
        assert out["species"] == 7
        assert out["moves"] == [33, 39, 145, 0]
        assert out["pp"] == [35, 30, 30, 0]
        assert out["evs"] == [1, 2, 3, 4, 5, 6]
        assert out["friendship"] == 70
        assert out["experience"] == 1000

    def test_decrypt_substructs_checksum_mismatch(self):
        """Corrupting one byte of the encrypted block should make the
        computed checksum not match the value the caller would compare."""
        from pokebenchmark_emulator.adapters._gen3_mon import decrypt_substructs

        personality = 0xCAFEBABE
        ot_id = 0xAABBCCDD
        substructs = _build_substructs_plaintext(
            species=25, held_item=0, experience=500, pp_bonuses=0,
            friendship=100, moves=[84, 0, 0, 0], pps=[30, 0, 0, 0],
            evs=[0] * 6, pokerus=0, met_location=0, origin=0, iv=0, ribbons=0,
        )
        encrypted, good_checksum = _encrypt_substruct_block(
            substructs, personality, ot_id
        )
        corrupted = bytearray(encrypted)
        corrupted[5] ^= 0xFF  # flip bits in a middle byte
        out = decrypt_substructs(bytes(corrupted), personality, ot_id)
        # decrypt_substructs always returns a dict; the caller checks
        # `computed_checksum` against its stored value. So verify the
        # computed checksum no longer matches.
        assert out is not None
        assert out["computed_checksum"] != good_checksum

    def test_read_gen3_party_mon_rejects_checksum_mismatch(self):
        """read_gen3_party_mon builds the struct itself and does the
        checksum compare — so a corrupted encrypted block yields None."""
        from pokebenchmark_emulator.adapters._gen3_mon import read_gen3_party_mon

        personality = 0x11111111
        ot_id = 0x22222222
        substructs = _build_substructs_plaintext(
            species=1, held_item=0, experience=100, pp_bonuses=0,
            friendship=50, moves=[33, 0, 0, 0], pps=[35, 0, 0, 0],
            evs=[0] * 6, pokerus=0, met_location=0, origin=0, iv=0, ribbons=0,
        )
        raw = bytearray(_build_party_mon_struct(
            personality, ot_id, b"BULBA", 5, 20, 20, 0, substructs,
        ))
        # Corrupt a byte in the encrypted block (0x20..0x50)
        raw[0x25] ^= 0x55

        mock_emu = MagicMock()
        mock_emu.read_memory.return_value = bytes(raw)
        result = read_gen3_party_mon(mock_emu, 0x02000000)
        assert result is None

    def test_species_name_known(self):
        from pokebenchmark_emulator.adapters._gen3_names import species_name
        assert species_name(1) == "Bulbasaur"
        assert species_name(25) == "Pikachu"
        assert species_name(151) == "Mew"
        assert species_name(277) == "Treecko"

    def test_species_name_fallback(self):
        from pokebenchmark_emulator.adapters._gen3_names import species_name
        # 252-276 are the placeholder "?" slots — not in our table.
        assert species_name(260) == "Species#260"
        # Wildly out-of-range also falls back.
        assert species_name(9999) == "Species#9999"

    def test_move_name_known(self):
        from pokebenchmark_emulator.adapters._gen3_names import move_name
        assert move_name(0) == "---"
        assert move_name(1) == "Pound"
        assert move_name(33) == "Tackle"
        assert move_name(354) == "Psycho Boost"

    def test_move_name_fallback(self):
        from pokebenchmark_emulator.adapters._gen3_names import move_name
        assert move_name(9999) == "Move#9999"

    def test_decode_status_healthy(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(0) is None

    def test_decode_status_sleep(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(3) == "sleep 3"
        assert decode_status(1) == "sleep 1"

    def test_decode_status_poison(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(0b00001000) == "psn"

    def test_decode_status_burn(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(0b00010000) == "brn"

    def test_decode_status_freeze(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(0b00100000) == "frz"

    def test_decode_status_paralysis(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(0b01000000) == "par"

    def test_decode_status_toxic(self):
        from pokebenchmark_emulator.adapters._gen3_mon import decode_status
        assert decode_status(0b10000000) == "tox"

    # ---- Integration: FireRedAdapter.read_state ----

    def _make_party_mock_emulator(self):
        """Mock emulator returning a FireRed save block with 1 party Pokemon.

        The party slot holds a Charmander (species 4), level 10, 28/30 HP,
        with moves Scratch/Growl/Ember/Leer.
        """
        SAVEBLOCK1_BASE = 0x02025000
        SAVEBLOCK2_BASE = 0x02024000
        SECURITY_KEY = 0xDEADBEEF
        MONEY_RAW_ENCODED = 3000 ^ SECURITY_KEY  # stored money = 3000

        personality = 0xABCDEF01
        ot_id = 0x5678
        substructs = _build_substructs_plaintext(
            species=4,  # Charmander
            held_item=0,
            experience=1000,
            pp_bonuses=0,
            friendship=70,
            moves=[10, 45, 52, 43],  # Scratch, Growl, Ember, Leer
            pps=[35, 40, 25, 30],
            evs=[0] * 6,
            pokerus=0,
            met_location=1,
            origin=0,
            iv=0,
            ribbons=0,
        )
        mon_bytes = _build_party_mon_struct(
            personality=personality,
            ot_id=ot_id,
            nickname_bytes=b"\xc7\xdc\xd8\xe3\xe3\xed\xff\xff\xff\xff",  # "Mickey" roughly
            level=10,
            hp=28,
            max_hp=30,
            status_u32=0,
            substructs=substructs,
        )

        mock_emu = MagicMock()

        def read_u32(addr):
            if addr == 0x03005008:
                return SAVEBLOCK1_BASE
            if addr == 0x0300500C:
                return SAVEBLOCK2_BASE
            if addr == SAVEBLOCK2_BASE + 0x0F20:
                return SECURITY_KEY
            if addr == SAVEBLOCK1_BASE + 0x0290:
                return MONEY_RAW_ENCODED
            return 0

        def read_u16(addr):
            if addr == SAVEBLOCK1_BASE + 0x00:
                return 5
            if addr == SAVEBLOCK1_BASE + 0x02:
                return 10
            return 0

        def read_u8(addr):
            if addr == SAVEBLOCK1_BASE + 0x04:
                return 3  # map group
            if addr == SAVEBLOCK1_BASE + 0x05:
                return 1  # map num -> Route 1
            if addr == SAVEBLOCK2_BASE + 0x08:
                return 0b00000001  # Boulder badge
            if addr == SAVEBLOCK1_BASE + 0x34:
                return 1  # party count = 1
            return 0

        def read_memory(addr, size):
            # Player name
            if addr == SAVEBLOCK2_BASE + 0x00:
                return bytes([0xCC, 0xBF, 0xBE, 0xFF, 0xFF, 0xFF, 0xFF])[:size]
            # Party slot 0
            if addr == SAVEBLOCK1_BASE + 0x38 and size == 100:
                return mon_bytes
            return bytes(size)

        mock_emu.read_u32.side_effect = read_u32
        mock_emu.read_u16.side_effect = read_u16
        mock_emu.read_u8.side_effect = read_u8
        mock_emu.read_memory.side_effect = read_memory
        return mock_emu

    def test_read_state_populates_party(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_party_mock_emulator()
        result = adapter.read_state(mock_emu)

        assert result.party is not None
        assert len(result.party) == 1
        mon = result.party[0]
        assert mon["species"] == "Charmander"
        assert mon["species_id"] == 4
        assert mon["level"] == 10
        assert mon["hp"] == 28
        assert mon["max_hp"] == 30
        assert mon["status"] is None
        assert mon["moves"] == ["Scratch", "Growl", "Ember", "Leer"]

    def test_read_state_populates_money(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_party_mock_emulator()
        result = adapter.read_state(mock_emu)

        assert result.money == 3000

    def test_read_state_in_battle_false(self):
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_party_mock_emulator()
        result = adapter.read_state(mock_emu)

        # We don't detect battles yet — best-effort false.
        assert result.in_battle is False
        assert result.battle_state is None
        assert result.bag is None
        assert result.dialog is None

    def test_read_state_money_cap_zeros_out(self):
        """If XOR'd money comes out > 999,999 the adapter should clamp to 0
        (uninitialized security key)."""
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_party_mock_emulator()
        # Override just the money reads to produce a huge value.
        SAVEBLOCK1_BASE = 0x02025000
        SAVEBLOCK2_BASE = 0x02024000

        def read_u32(addr):
            if addr == 0x03005008:
                return SAVEBLOCK1_BASE
            if addr == 0x0300500C:
                return SAVEBLOCK2_BASE
            if addr == SAVEBLOCK2_BASE + 0x0F20:
                return 0  # security key uninitialized
            if addr == SAVEBLOCK1_BASE + 0x0290:
                return 0xFFFFFFFF  # huge raw value
            return 0

        mock_emu.read_u32.side_effect = read_u32
        result = adapter.read_state(mock_emu)
        assert result.money == 0

    def test_read_state_empty_party_slot(self):
        """A party count of 0 should give an empty list (not None)."""
        from pokebenchmark_emulator.adapters.firered import FireRedAdapter

        adapter = FireRedAdapter()
        mock_emu = self._make_party_mock_emulator()
        SAVEBLOCK1_BASE = 0x02025000
        SAVEBLOCK2_BASE = 0x02024000

        def read_u8(addr):
            if addr == SAVEBLOCK1_BASE + 0x04:
                return 3
            if addr == SAVEBLOCK1_BASE + 0x05:
                return 1
            if addr == SAVEBLOCK2_BASE + 0x08:
                return 0
            if addr == SAVEBLOCK1_BASE + 0x34:
                return 0  # party empty
            return 0

        mock_emu.read_u8.side_effect = read_u8
        result = adapter.read_state(mock_emu)
        assert result.party == []
