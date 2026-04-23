"""FireRed adapter — reads game state directly from GBA memory via DMA pointer chasing."""
from .base import BattleState, GameAdapter, GameState

# DMA pointer addresses in IWRAM
SAVEBLOCK1_PTR = 0x03005008
SAVEBLOCK2_PTR = 0x0300500C

# Offsets within SaveBlock1
SB1_X_OFFSET = 0x00         # u16
SB1_Y_OFFSET = 0x02         # u16
SB1_MAPGROUP_OFFSET = 0x04  # u8
SB1_MAPNUM_OFFSET = 0x05    # u8

# Offsets within SaveBlock2
SB2_PLAYERNAME_OFFSET = 0x00  # 7 bytes (up to 7 chars + terminator)
SB2_PLAYERNAME_LENGTH = 7
SB2_BADGES_OFFSET = 0x08     # u8 — bitmask of badges
SB2_SECURITY_KEY_OFFSET = 0x0F20  # u32 — FireRed money XOR key

# Offsets within SaveBlock1 for party + money
SB1_PARTY_COUNT_OFFSET = 0x34       # u8, 0..6
SB1_PARTY_OFFSET = 0x38             # 6 × 100-byte PokemonStruct
SB1_MONEY_OFFSET = 0x0290           # u32, XOR'd with security key
GEN3_PARTY_MON_SIZE = 100
GEN3_PARTY_MAX = 6
MONEY_CAP = 999_999

# Badge names for FireRed (Kanto order)
FIRERED_BADGE_NAMES = [
    "Boulder",
    "Cascade",
    "Thunder",
    "Rainbow",
    "Soul",
    "Marsh",
    "Volcano",
    "Earth",
]

# FireRed / Gen 3 character encoding (same as Emerald)
# Maps byte value -> character string
FIRERED_CHARMAP: dict[int, str] = {
    0x00: " ",
    0x01: "À",
    0x02: "Á",
    0x03: "Â",
    0x04: "Ç",
    0x05: "È",
    0x06: "É",
    0x07: "Ê",
    0x08: "Ë",
    0x09: "Ì",
    0x0B: "Î",
    0x0C: "Ï",
    0x0D: "Ò",
    0x0E: "Ó",
    0x0F: "Ô",
    0x10: "Œ",
    0x11: "Ù",
    0x12: "Ú",
    0x13: "Û",
    0x14: "Ñ",
    0x15: "ß",
    0x16: "à",
    0x17: "á",
    0x19: "ç",
    0x1A: "è",
    0x1B: "é",
    0x1C: "ê",
    0x1D: "ë",
    0x1E: "ì",
    0x20: "î",
    0x21: "ï",
    0x22: "ò",
    0x23: "ó",
    0x24: "ô",
    0x25: "œ",
    0x26: "ù",
    0x27: "ú",
    0x28: "û",
    0x29: "ñ",
    0x2A: "º",
    0x2B: "ª",
    0x2D: "&",
    0x2E: "+",
    0x34: "Lv",
    0x35: "=",
    0x36: ";",
    0xA1: "0",
    0xA2: "1",
    0xA3: "2",
    0xA4: "3",
    0xA5: "4",
    0xA6: "5",
    0xA7: "6",
    0xA8: "7",
    0xA9: "8",
    0xAA: "9",
    0xAB: "!",
    0xAC: "?",
    0xAD: ".",
    0xAE: "-",
    0xB0: "…",
    0xB1: "\u201c",
    0xB2: "\u201d",
    0xB3: "\u2018",
    0xB4: "\u2019",
    0xB5: "♂",
    0xB6: "♀",
    0xB7: "$",
    0xB8: ",",
    0xB9: "×",
    0xBA: "/",
    0xBB: "A",
    0xBC: "B",
    0xBD: "C",
    0xBE: "D",
    0xBF: "E",
    0xC0: "F",
    0xC1: "G",
    0xC2: "H",
    0xC3: "I",
    0xC4: "J",
    0xC5: "K",
    0xC6: "L",
    0xC7: "M",
    0xC8: "N",
    0xC9: "O",
    0xCA: "P",
    0xCB: "Q",
    0xCC: "R",
    0xCD: "S",
    0xCE: "T",
    0xCF: "U",
    0xD0: "V",
    0xD1: "W",
    0xD2: "X",
    0xD3: "Y",
    0xD4: "Z",
    0xD5: "a",
    0xD6: "b",
    0xD7: "c",
    0xD8: "d",
    0xD9: "e",
    0xDA: "f",
    0xDB: "g",
    0xDC: "h",
    0xDD: "i",
    0xDE: "j",
    0xDF: "k",
    0xE0: "l",
    0xE1: "m",
    0xE2: "n",
    0xE3: "o",
    0xE4: "p",
    0xE5: "q",
    0xE6: "r",
    0xE7: "s",
    0xE8: "t",
    0xE9: "u",
    0xEA: "v",
    0xEB: "w",
    0xEC: "x",
    0xED: "y",
    0xEE: "z",
    0xEF: "▶",
    0xF0: ":",
    0xF1: "Ä",
    0xF2: "Ö",
    0xF3: "Ü",
    0xF4: "ä",
    0xF5: "ö",
    0xF6: "ü",
}

# 0xFF is the string terminator and is intentionally not in the charmap

# Map (mapGroup, mapNum) -> location name for FireRed (Kanto)
FIRERED_MAP_NAMES: dict[tuple[int, int], str] = {
    (0, 0): "Pallet Town",
    (0, 1): "Viridian City",
    (0, 2): "Pewter City",
    (0, 3): "Cerulean City",
    (0, 4): "Lavender Town",
    (0, 5): "Vermilion City",
    (0, 6): "Celadon City",
    (0, 7): "Fuchsia City",
    (0, 8): "Cinnabar Island",
    (0, 9): "Indigo Plateau",
    (0, 10): "Saffron City",
    (3, 1): "Route 1",
    (3, 2): "Route 2",
    (3, 3): "Route 3",
    (3, 4): "Route 4",
    (3, 5): "Route 5",
    (3, 6): "Route 6",
    (3, 7): "Route 7",
    (3, 8): "Route 8",
    (3, 9): "Route 9",
    (3, 10): "Route 10",
    (3, 11): "Route 11",
    (3, 12): "Route 12",
    (3, 13): "Route 13",
    (3, 14): "Route 14",
    (3, 15): "Route 15",
    (3, 16): "Route 16",
    (3, 17): "Route 17",
    (3, 18): "Route 18",
    (3, 19): "Route 19",
    (3, 20): "Route 20",
    (3, 21): "Route 21",
    (3, 22): "Route 22",
    (3, 23): "Route 23",
    (3, 24): "Route 24",
    (3, 25): "Route 25",
}


def decode_string(data: bytes) -> str:
    """Decode a Gen 3 encoded byte string, stopping at the 0xFF terminator."""
    result = []
    for byte in data:
        if byte == 0xFF:
            break
        char = FIRERED_CHARMAP.get(byte)
        if char is not None:
            result.append(char)
        # Unknown/unmapped bytes are silently skipped
    return "".join(result)


class FireRedAdapter(GameAdapter):
    """Reads game state from Pokemon FireRed via direct memory reads with DMA pointer chasing."""

    @property
    def game_name(self) -> str:
        return "firered"

    def read_state(self, emulator) -> GameState:
        # Chase DMA pointers to find save block bases
        sb1_base = emulator.read_u32(SAVEBLOCK1_PTR)
        sb2_base = emulator.read_u32(SAVEBLOCK2_PTR)

        # Read player name from SaveBlock2
        name_bytes = emulator.read_memory(sb2_base + SB2_PLAYERNAME_OFFSET, SB2_PLAYERNAME_LENGTH)
        player_name = decode_string(name_bytes)

        # Read coordinates from SaveBlock1
        x = emulator.read_u16(sb1_base + SB1_X_OFFSET)
        y = emulator.read_u16(sb1_base + SB1_Y_OFFSET)

        # Read map group/num from SaveBlock1
        map_group = emulator.read_u8(sb1_base + SB1_MAPGROUP_OFFSET)
        map_num = emulator.read_u8(sb1_base + SB1_MAPNUM_OFFSET)
        location = FIRERED_MAP_NAMES.get((map_group, map_num), f"Map({map_group},{map_num})")

        # Read badge bitmask from SaveBlock2
        badge_byte = emulator.read_u8(sb2_base + SB2_BADGES_OFFSET)
        badges = [
            FIRERED_BADGE_NAMES[i]
            for i in range(8)
            if (badge_byte >> i) & 1
        ]

        # Import here to avoid a circular import at module load (the helper
        # module imports `decode_string` from this file).
        from ._gen3_mon import read_gen3_party_mon

        # Read party
        party: list[dict] = []
        try:
            party_count = emulator.read_u8(sb1_base + SB1_PARTY_COUNT_OFFSET)
            for i in range(min(party_count, GEN3_PARTY_MAX)):
                slot_addr = sb1_base + SB1_PARTY_OFFSET + (i * GEN3_PARTY_MON_SIZE)
                mon = read_gen3_party_mon(emulator, slot_addr)
                if mon is not None:
                    party.append(mon)
        except Exception:
            # If a read fails mid-party we return what we have rather than
            # exploding the whole state read.
            pass

        # Read money (XOR'd with security key)
        try:
            security_key = emulator.read_u32(sb2_base + SB2_SECURITY_KEY_OFFSET)
            money_raw = emulator.read_u32(sb1_base + SB1_MONEY_OFFSET)
            money = (money_raw ^ security_key) & 0xFFFFFFFF
            if money > MONEY_CAP:
                # Either the security key isn't initialized yet (fresh save,
                # pre-intro) or we're looking at garbage — game caps at
                # 999,999 so any higher value is by definition wrong.
                money = 0
        except Exception:
            money = None

        return GameState(
            player_name=player_name,
            location=location,
            x=x,
            y=y,
            facing="unknown",
            badges=badges,
            money=money,
            party=party,
            in_battle=False,
            # bag / dialog / battle_state left as None — not extracted yet.
        )
