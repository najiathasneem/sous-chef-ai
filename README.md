# Sous-Chef AI

Software brain for a home AI cooking machine (one-pot dishes: dal, curry, soups).
Phase 1 runs entirely on your PC with a **simulated machine**, so there's no hardware and no fire risk.

## Quick start
```bash
python main.py run recipes/simple_dal.json   # cook dal on the simulator (~1 sec)
python main.py run recipes/simple_dal.json --plot cook.png   # + temperature graph (pip install matplotlib)
python -m unittest -v                        # run the tests
```

AI recipes (optional):
```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python main.py ai "chana masala for 4" --save recipes/chana.json --cook
```

## How it's built
```
souschef/
  hardware.py   abstract interfaces: Heater, TempSensor, Stirrer, Scale, Dispenser, Clock
  simulator.py  fake versions + a physics model of the pot (heating, cooling, boiling)
  engine.py     runs a recipe step by step; PID temperature control; safety stops
  pid.py        PID controller for holding temperatures
  recipe.py     JSON recipe format + validation (temp/rpm limits, slots, steps)
  ai.py         Claude turns a plain request into a validated recipe
  plot.py       graph of temperature, heater power and stirring over time
recipes/        example recipes
tests/          unit tests
```

The engine only uses the interfaces in `hardware.py`. To move to a Raspberry Pi, write
real classes (relay for the heater, MAX31855 thermocouple, HX711 load cell, servos)
with the same methods. Nothing else changes.

## Recipe actions
| action | fields | what it does |
|---|---|---|
| `heat` | `target_c` | full power until the temperature is reached |
| `hold` | `target_c`, `seconds`, `stir_rpm`? | keep a temperature (PID) while stirring |
| `add`  | `slot`, `grams` | open a hopper until the scale shows the weight |
| `stir` | `rpm`, `seconds` | stir only |
| `wait` | `seconds` | heat off, rest |
| `done` | | everything off |

## Safety built in
- Stops and turns everything off if the temperature sensor fails or the pot overheats
- Gives up if a temperature isn't reached in 20 min, or a hopper jams or runs empty
- Rejects recipes over 230 °C or 80 rpm, or that use empty slots (including AI-written ones)

## Roadmap
1. ✅ Simulator + engine + AI recipes
2. Raspberry Pi + real sensor/motor/servo (test with water only)
3. Induction cooktop control + camera
4. Vision for doneness (e.g. "onions golden?") and learning from family ratings
