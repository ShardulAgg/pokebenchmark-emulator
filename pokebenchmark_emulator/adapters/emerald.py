"""Emerald adapter — wraps pygba's get_game_state into our GameState format."""
from pygba.game_wrappers.pokemon_emerald import get_game_state, read_save_block_2

from .base import BattleState, GameAdapter, GameState

# Badge names in Emerald order (Stone -> Rain)
EMERALD_BADGE_NAMES = [
    "Stone",
    "Knuckle",
    "Dynamo",
    "Heat",
    "Balance",
    "Feather",
    "Mind",
    "Rain",
]

# Map (mapGroup, mapNum) -> human-readable location name
# Covers the 16 cities/towns from pygba's visited_cities plus key routes
EMERALD_MAP_NAMES: dict[tuple[int, int], str] = {
    (0, 0): "Littleroot Town",
    (0, 1): "Oldale Town",
    (0, 2): "Dewford Town",
    (0, 3): "Lavaridge Town",
    (0, 4): "Fallarbor Town",
    (0, 5): "Verdanturf Town",
    (0, 6): "Pacifidlog Town",
    (1, 0): "Petalburg City",
    (1, 1): "Slateport City",
    (1, 2): "Mauville City",
    (1, 3): "Rustboro City",
    (1, 4): "Fortree City",
    (1, 5): "Lilycove City",
    (1, 6): "Mossdeep City",
    (1, 7): "Sootopolis City",
    (1, 8): "Ever Grande City",
    (2, 0): "Route 101",
    (2, 1): "Route 102",
    (2, 2): "Route 103",
    (2, 3): "Route 104",
    (2, 4): "Route 105",
    (2, 5): "Route 106",
    (2, 6): "Route 107",
    (2, 7): "Route 108",
    (2, 8): "Route 109",
    (2, 9): "Route 110",
    (2, 10): "Route 111",
    (2, 11): "Route 112",
    (2, 12): "Route 113",
    (2, 13): "Route 114",
    (2, 14): "Route 115",
    (2, 15): "Route 116",
    (2, 16): "Route 117",
    (2, 17): "Route 118",
    (2, 18): "Route 119",
    (2, 19): "Route 120",
    (2, 20): "Route 121",
    (2, 21): "Route 122",
    (2, 22): "Route 123",
    (2, 23): "Route 124",
    (2, 24): "Route 125",
    (2, 25): "Route 126",
    (2, 26): "Route 127",
    (2, 27): "Route 128",
    (2, 28): "Route 129",
    (2, 29): "Route 130",
    (2, 30): "Route 131",
    (2, 31): "Route 132",
    (2, 32): "Route 133",
    (2, 33): "Route 134",
}


def _parse_party(raw_party: list) -> list[dict]:
    """Convert pygba's raw party list into our party format."""
    result = []
    for mon in raw_party:
        if mon is None:
            continue
        box = mon.get("box")
        if box is None:
            continue

        substructs = box.get("substructs", ())
        species_id = 0
        move_ids: list[int] = []
        if len(substructs) >= 1:
            sub0 = substructs[0]
            if isinstance(sub0, dict):
                species_id = sub0.get("species", 0)
        if len(substructs) >= 2:
            sub1 = substructs[1]
            if isinstance(sub1, dict):
                move_ids = sub1.get("moves", [])

        nickname = box.get("nickname", "")
        species_str = nickname if nickname else f"#{species_id}"

        result.append({
            "species": species_str,
            "level": mon.get("level", 0),
            "hp": mon.get("hp", 0),
            "max_hp": mon.get("maxHp", 0),
            "moves": [f"Move#{mid}" for mid in move_ids if mid != 0],
        })
    return result


class EmeraldAdapter(GameAdapter):
    """Reads game state from Pokemon Emerald via pygba's get_game_state."""

    @property
    def game_name(self) -> str:
        return "emerald"

    def read_state(self, emulator) -> GameState:
        state = get_game_state(emulator.gba)
        sb2 = read_save_block_2(emulator.gba)

        # Player name
        player_name: str = ""
        if sb2 is not None:
            raw_name = sb2.get("playerName", "")
            # playerName may be raw bytes or already decoded string
            if isinstance(raw_name, (bytes, bytearray)):
                from pygba.game_wrappers.pokemon_emerald import EmeraldCharmap
                player_name = EmeraldCharmap().decode(raw_name)
            else:
                player_name = str(raw_name)

        # Position
        pos = state.get("pos", {})
        x = pos.get("x", 0)
        y = pos.get("y", 0)

        # Location
        location_data = state.get("location", {})
        map_group = location_data.get("mapGroup", 0)
        map_num = location_data.get("mapNum", 0)
        location = EMERALD_MAP_NAMES.get((map_group, map_num), f"Map({map_group},{map_num})")

        # Facing — not directly available from get_game_state; default to unknown
        facing = "unknown"

        # Badges — list of 8 booleans
        raw_badges: list = state.get("badges", [False] * 8)
        badges = [
            EMERALD_BADGE_NAMES[i]
            for i, has_badge in enumerate(raw_badges)
            if has_badge and i < len(EMERALD_BADGE_NAMES)
        ]

        # Money
        money = state.get("money", 0)

        # Party
        raw_party = state.get("party", [])
        party = _parse_party(raw_party)

        # Bag — not returned by get_game_state by default (requires parse_items=True)
        bag: list[dict] = []

        # Dialog — not available from get_game_state
        dialog = ""

        # Battle — not available from get_game_state
        in_battle = False
        battle_state = None

        return GameState(
            player_name=player_name,
            location=location,
            x=x,
            y=y,
            facing=facing,
            badges=badges,
            money=money,
            party=party,
            bag=bag,
            dialog=dialog,
            in_battle=in_battle,
            battle_state=battle_state,
        )
