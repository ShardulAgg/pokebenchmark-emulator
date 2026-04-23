from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class BattleState:
    is_wild: bool
    enemy_species: str
    enemy_level: int
    enemy_hp: int
    enemy_max_hp: int
    enemy_types: list[str] = field(default_factory=list)


@dataclass
class GameState:
    """Game state read by an adapter.

    Only the first five fields are considered broadly universal. Everything
    else defaults to None: adapters populate what they actually read, and
    consumers can distinguish "not populated" from "populated as empty".
    """
    player_name: str
    location: str
    x: int
    y: int
    facing: str
    badges: list[str] | None = None
    money: int | None = None
    party: list[dict] | None = None
    bag: list[dict] | None = None
    dialog: str | None = None
    in_battle: bool | None = None
    battle_state: BattleState | None = None

    def to_text(self) -> str:
        lines = []
        lines.append(f"Player: {self.player_name}")
        lines.append(f"Location: {self.location} ({self.x}, {self.y}) facing {self.facing}")
        if self.money is not None:
            lines.append(f"Money: ${self.money}")
        if self.badges is not None:
            lines.append(f"Badges: {', '.join(self.badges) if self.badges else 'none'}")
        if self.party is not None:
            lines.append("")
            lines.append("Party:")
            if self.party:
                for mon in self.party:
                    hp_str = f"{mon.get('hp', '?')}/{mon.get('max_hp', '?')}"
                    moves = ", ".join(mon.get("moves", []))
                    lines.append(f"  {mon.get('species', '?')} Lv{mon.get('level', '?')} HP:{hp_str} [{moves}]")
            else:
                lines.append("  (empty)")
        if self.bag is not None:
            lines.append("")
            lines.append("Bag:")
            if self.bag:
                for item in self.bag:
                    lines.append(f"  {item.get('item', '?')} x{item.get('quantity', '?')}")
            else:
                lines.append("  (empty)")
        if self.dialog:
            lines.append("")
            lines.append(f"Dialog: {self.dialog}")
        if self.in_battle and self.battle_state:
            bs = self.battle_state
            battle_type = "Wild" if bs.is_wild else "Trainer"
            lines.append("")
            lines.append(f"Battle ({battle_type}): {bs.enemy_species} Lv{bs.enemy_level} HP:{bs.enemy_hp}/{bs.enemy_max_hp}")
        return "\n".join(lines)


class GameAdapter(ABC):
    @property
    @abstractmethod
    def game_name(self) -> str: ...

    @abstractmethod
    def read_state(self, emulator) -> GameState: ...
