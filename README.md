# pokebenchmark-emulator

GBA emulator wrapper + Pokemon Gen 3 game state adapters.

Part of the [pokebenchmark](https://github.com/ShardulAgg/pokebenchmark-platform) benchmarking framework for LLM agents playing Pokemon on the Game Boy Advance.

## What's here

- `GBAEmulator` — a thin Python wrapper around [pygba](https://github.com/dvruette/pygba) exposing button input, memory reads, screenshots, and save/load states.
- Game adapters (`FireRedAdapter`, `EmeraldAdapter`) that parse emulator memory into a unified `GameState` dataclass.

## Install

```bash
pip install pokebenchmark-emulator
```

Requires `mgba` Python bindings (built from source — see the [pokebenchmark Dockerfile](https://github.com/ShardulAgg/pokebenchmark-platform/blob/main/Dockerfile) for a working build recipe).

## Usage

```python
from pokebenchmark_emulator import GBAEmulator
from pokebenchmark_emulator.adapters import FireRedAdapter

emu = GBAEmulator("firered.gba")
emu.wait(3600)                   # boot past title screen

adapter = FireRedAdapter()
state = adapter.read_state(emu)
print(state.to_text())

emu.press_button("A")
img = emu.screenshot()           # PIL.Image
raw = emu.save_state()           # bytes
```

## Supported games

- Pokémon FireRed (`FireRedAdapter`) — DMA-pointer-chased state: position, map, badges, player name
- Pokémon Emerald (`EmeraldAdapter`) — wraps pygba's built-in game_state: party, badges, money, location

## Extending

Add a new game by implementing `GameAdapter` from `pokebenchmark_emulator.adapters.base`. Two methods to implement: `game_name` and `read_state(emulator) -> GameState`.

## License

MIT
