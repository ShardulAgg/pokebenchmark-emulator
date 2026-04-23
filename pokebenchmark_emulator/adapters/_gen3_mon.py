"""Gen 3 party Pokemon struct decoding.

A Gen 3 party Pokemon is a 100-byte structure laid out as:
  0x00  u32  personality value (PID)
  0x04  u32  OT ID
  0x08  10B  nickname (Gen 3 charmap)
  0x12  u8   language
  0x13  u8   misc flags
  0x14  7B   OT name
  0x1B  u8   markings
  0x1C  u16  checksum of decrypted substructs
  0x1E  u16  unknown
  0x20  48B  *encrypted* substruct block (four 12-byte substructs, shuffled)
  0x50  u32  status condition (only low byte is used)
  0x54  u8   level
  0x55  u8   pokerus / mail id
  0x56  u16  current HP
  0x58  u16  max HP
  0x5A..0x63  stats (atk/def/spe/spatk/spdef)

The 48-byte encrypted block is four 12-byte substructs in one of 24 orderings
determined by (personality % 24). Each u32 in the block is XOR'd with
(personality XOR ot_id).

After decryption, the 24 u16 values in the 48-byte block (little-endian)
summed (masked to u16) must equal the stored checksum. This is the
integrity check we use to detect empty / corrupted slots — if it fails,
we treat the slot as empty.
"""
from __future__ import annotations

import struct

from .firered import decode_string
from ._gen3_names import move_name, species_name


# 24 permutations of the 4 substructs (G=Growth, A=Attacks, E=EVs/condition,
# M=Misc). The index into this table is (personality % 24). Each entry
# describes the order the substructs appear in the *encrypted* block —
# so to unshuffle, we read block position i and place its contents into
# the substruct named by SUBSTRUCT_ORDER[perm][i].
#
# Source: pret/pokeemerald and pret/pokefirered `include/pokemon.h`
# (the `gSubstructOrder` table in game code).
SUBSTRUCT_ORDER: tuple[tuple[str, str, str, str], ...] = (
    ("G", "A", "E", "M"),  # 0
    ("G", "A", "M", "E"),  # 1
    ("G", "E", "A", "M"),  # 2
    ("G", "E", "M", "A"),  # 3
    ("G", "M", "A", "E"),  # 4
    ("G", "M", "E", "A"),  # 5
    ("A", "G", "E", "M"),  # 6
    ("A", "G", "M", "E"),  # 7
    ("A", "E", "G", "M"),  # 8
    ("A", "E", "M", "G"),  # 9
    ("A", "M", "G", "E"),  # 10
    ("A", "M", "E", "G"),  # 11
    ("E", "G", "A", "M"),  # 12
    ("E", "G", "M", "A"),  # 13
    ("E", "A", "G", "M"),  # 14
    ("E", "A", "M", "G"),  # 15
    ("E", "M", "G", "A"),  # 16
    ("E", "M", "A", "G"),  # 17
    ("M", "G", "A", "E"),  # 18
    ("M", "G", "E", "A"),  # 19
    ("M", "A", "G", "E"),  # 20
    ("M", "A", "E", "G"),  # 21
    ("M", "E", "G", "A"),  # 22
    ("M", "E", "A", "G"),  # 23
)


# Status flags for the low byte of the u32 at PokemonStruct + 0x50
STATUS_SLEEP_MASK = 0b00000111  # bits 0-2 = sleep turns remaining
STATUS_POISON = 0b00001000  # bit 3
STATUS_BURN = 0b00010000  # bit 4
STATUS_FREEZE = 0b00100000  # bit 5
STATUS_PARALYSIS = 0b01000000  # bit 6
STATUS_TOXIC = 0b10000000  # bit 7


def decode_status(status_u8: int) -> str | None:
    """Decode the low byte of the status u32 into a short label.

    0 -> None (healthy)
    sleep turns > 0 -> "sleep N"
    poisoned -> "psn", burned -> "brn", frozen -> "frz",
    paralyzed -> "par", badly poisoned -> "tox".

    If multiple bits are set (rare / impossible during normal gameplay),
    toxic takes precedence, then freeze, burn, paralysis, poison, sleep.
    """
    s = status_u8 & 0xFF
    if s == 0:
        return None
    if s & STATUS_TOXIC:
        return "tox"
    if s & STATUS_FREEZE:
        return "frz"
    if s & STATUS_BURN:
        return "brn"
    if s & STATUS_PARALYSIS:
        return "par"
    if s & STATUS_POISON:
        return "psn"
    sleep_turns = s & STATUS_SLEEP_MASK
    if sleep_turns:
        return f"sleep {sleep_turns}"
    return None


def decrypt_substructs(encrypted: bytes, personality: int, ot_id: int) -> dict | None:
    """Decrypt + unshuffle the 48-byte encrypted substruct block.

    Returns a dict with the merged G/A/E/M substruct fields, or None if
    the checksum does not match the decrypted data.
    """
    if len(encrypted) != 48:
        raise ValueError(f"encrypted block must be 48 bytes, got {len(encrypted)}")

    key = (personality ^ ot_id) & 0xFFFFFFFF

    # Decrypt: XOR each u32 with the key. The result is the *shuffled*
    # plaintext, still in the block's on-disk order.
    decrypted = bytearray(48)
    for i in range(12):
        enc_u32 = struct.unpack_from("<I", encrypted, i * 4)[0]
        dec_u32 = (enc_u32 ^ key) & 0xFFFFFFFF
        struct.pack_into("<I", decrypted, i * 4, dec_u32)

    # Checksum: sum of 24 little-endian u16s in the decrypted block,
    # masked to u16. If it doesn't match the caller's stored checksum,
    # the caller treats this slot as corrupt. We return the computed
    # checksum in the dict so the caller can compare.
    checksum = 0
    for i in range(24):
        checksum = (checksum + struct.unpack_from("<H", decrypted, i * 2)[0]) & 0xFFFF

    # Unshuffle: which 12-byte slot holds G, A, E, M?
    perm = SUBSTRUCT_ORDER[personality % 24]
    slots: dict[str, bytes] = {}
    for block_index, substruct_name in enumerate(perm):
        start = block_index * 12
        slots[substruct_name] = bytes(decrypted[start : start + 12])

    # Parse each substruct.
    g = slots["G"]
    species = struct.unpack_from("<H", g, 0)[0]
    held_item = struct.unpack_from("<H", g, 2)[0]
    experience = struct.unpack_from("<I", g, 4)[0]
    pp_bonuses = g[8]
    friendship = g[9]

    a = slots["A"]
    moves = [struct.unpack_from("<H", a, i * 2)[0] for i in range(4)]
    pp = [a[8 + i] for i in range(4)]

    e = slots["E"]
    evs = list(e[0:6])  # HP, Atk, Def, Speed, SpAtk, SpDef

    m = slots["M"]
    pokerus = m[0]
    met_location = m[1]
    origin = struct.unpack_from("<H", m, 2)[0]
    iv = struct.unpack_from("<I", m, 4)[0]
    ribbons = struct.unpack_from("<I", m, 8)[0]

    return {
        "species": species,
        "held_item": held_item,
        "experience": experience,
        "pp_bonuses": pp_bonuses,
        "friendship": friendship,
        "moves": moves,
        "pp": pp,
        "evs": evs,
        "pokerus": pokerus,
        "met_location": met_location,
        "origin": origin,
        "iv": iv,
        "egg": (iv >> 30) & 1,  # egg flag lives in the IV u32 high bits
        "ribbons": ribbons,
        "computed_checksum": checksum,
    }


def read_gen3_party_mon(emulator, base_addr: int) -> dict | None:
    """Read one 100-byte party slot and return the rich dict described in
    the task spec, or None if the slot is empty / corrupt.

    Uses `emulator.read_memory(addr, size)` for the whole struct in one
    call to minimize round-trips.
    """
    raw = emulator.read_memory(base_addr, 100)
    if raw is None or len(raw) < 100:
        return None

    personality = struct.unpack_from("<I", raw, 0x00)[0]
    ot_id = struct.unpack_from("<I", raw, 0x04)[0]

    # Completely empty slot: PID of 0 and OT_ID of 0 is how the game marks
    # unused party slots. (PID=0 is not a legal value for a real Pokemon.)
    if personality == 0 and ot_id == 0:
        return None

    nickname_bytes = bytes(raw[0x08:0x12])
    nickname = decode_string(nickname_bytes)

    stored_checksum = struct.unpack_from("<H", raw, 0x1C)[0]
    encrypted = bytes(raw[0x20:0x50])

    decrypted = decrypt_substructs(encrypted, personality, ot_id)
    if decrypted is None:
        return None
    if decrypted["computed_checksum"] != stored_checksum:
        # Either corrupt or this slot is uninitialized garbage.
        return None

    species_id = decrypted["species"]
    if species_id == 0:
        # SPECIES_NONE after a valid decrypt -> empty slot
        return None

    status_u32 = struct.unpack_from("<I", raw, 0x50)[0]
    status = decode_status(status_u32 & 0xFF)
    level = raw[0x54]
    hp = struct.unpack_from("<H", raw, 0x56)[0]
    max_hp = struct.unpack_from("<H", raw, 0x58)[0]

    move_ids = decrypted["moves"]
    moves = [move_name(mid) for mid in move_ids]

    return {
        "species_id": species_id,
        "species": species_name(species_id),
        "nickname": nickname,
        "level": level,
        "hp": hp,
        "max_hp": max_hp,
        "status": status,
        "moves": moves,
        "move_ids": move_ids,
        "friendship": decrypted["friendship"],
        "experience": decrypted["experience"],
        "held_item_id": decrypted["held_item"],
    }
