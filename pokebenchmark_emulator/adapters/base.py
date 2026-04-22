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
    player_name: str
    location: str
    x: int
    y: int
    facing: str
    badges: list[str]
    money: int
    party: list[dict]
    bag: list[dict]
    dialog: str
    in_battle: bool
    battle_state: BattleState | None = None

    def to_text(self) -> str:
        lines = []
        lines.append(f"Player: {self.player_name}")
        lines.append(f"Location: {self.location} ({self.x}, {self.y}) facing {self.facing}")
        lines.append(f"Money: ${self.money}")
        if self.badges:
            lines.append(f"Badges: {', '.join(self.badges)}")
        else:
            lines.append("Badges: none")
        lines.append("")
        lines.append("Party:")
        for mon in self.party:
            hp_str = f"{mon.get('hp', '?')}/{mon.get('max_hp', '?')}"
            moves = ", ".join(mon.get("moves", []))
            lines.append(f"  {mon.get('species', '?')} Lv{mon.get('level', '?')} HP:{hp_str} [{moves}]")
        if not self.party:
            lines.append("  (empty)")
        lines.append("")
        lines.append("Bag:")
        for item in self.bag:
            lines.append(f"  {item.get('item', '?')} x{item.get('quantity', '?')}")
        if not self.bag:
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
