"""A fake machine so you can test everything on your PC.

It models a pot heating up on an induction plate, losing heat to the room,
cooling down when cold ingredients go in, and staying at ~100 C once there
is water in it.
"""
from .hardware import Clock, Heater, TempSensor, Stirrer, Scale, Dispenser, Machine

AMBIENT_C = 25.0
HEATER_WATTS = 1800.0
EFFICIENCY = 0.85
POT_HEAT_CAPACITY = 1800.0   # J/K for an empty steel pot (~4 kg-ish)
FOOD_HEAT_CAPACITY = 3.5     # J/(g*K), roughly food/water
LOSS_W_PER_K = 6.0           # heat lost to the room per degree above ambient
DISPENSE_G_PER_S = 25.0      # how fast a hopper pours


class SimPot:
    def __init__(self, slots: dict[int, dict]):
        self.temp_c = AMBIENT_C
        self.food_g = 0.0
        self.has_water = False
        self.power = 0.0
        self.rpm = 0
        self.open_slots: set[int] = set()
        self.slots = slots            # {slot: {"name":..., "liquid": bool}}
        self.sensor_broken = False
        self.time_s = 0.0
        # (time_s, temp_c, power 0-1, rpm, food_g), sampled for graphs
        self.history: list[tuple[float, float, float, int, float]] = []
        self._next_sample = 0.0

    def step(self, dt: float) -> None:
        self.time_s += dt
        if self.time_s >= self._next_sample:
            self.history.append((self.time_s, self.temp_c, self.power, self.rpm, self.food_g))
            self._next_sample += 2.0
        # pour from open hoppers (cold ingredients cool the pot)
        for slot in self.open_slots:
            grams = DISPENSE_G_PER_S * dt
            c_before = self._heat_capacity()
            self.food_g += grams
            self.temp_c = (c_before * self.temp_c
                           + grams * FOOD_HEAT_CAPACITY * AMBIENT_C) / self._heat_capacity()
            if self.slots.get(slot, {}).get("liquid"):
                self.has_water = True

        heat_in = self.power * HEATER_WATTS * EFFICIENCY
        heat_out = LOSS_W_PER_K * (self.temp_c - AMBIENT_C)
        self.temp_c += (heat_in - heat_out) * dt / self._heat_capacity()
        if self.has_water:
            self.temp_c = min(self.temp_c, 100.0)   # boiling point

    def _heat_capacity(self) -> float:
        return POT_HEAT_CAPACITY + self.food_g * FOOD_HEAT_CAPACITY


class SimClock(Clock):
    def __init__(self, pot: SimPot, tick: float = 0.5):
        self.t = 0.0
        self.pot = pot
        self.tick = tick

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        remaining = seconds
        while remaining > 1e-9:
            dt = min(self.tick, remaining)
            self.pot.step(dt)
            self.t += dt
            remaining -= dt


class SimHeater(Heater):
    def __init__(self, pot: SimPot):
        self.pot = pot

    def set_power(self, fraction: float) -> None:
        self.pot.power = max(0.0, min(1.0, fraction))


class SimTempSensor(TempSensor):
    def __init__(self, pot: SimPot):
        self.pot = pot

    def read_c(self) -> float | None:
        return None if self.pot.sensor_broken else self.pot.temp_c


class SimStirrer(Stirrer):
    def __init__(self, pot: SimPot):
        self.pot = pot

    def set_rpm(self, rpm: int) -> None:
        self.pot.rpm = rpm


class SimScale(Scale):
    def __init__(self, pot: SimPot):
        self.pot = pot

    def read_grams(self) -> float:
        return self.pot.food_g


class SimDispenser(Dispenser):
    def __init__(self, pot: SimPot):
        self.pot = pot

    def open(self, slot: int) -> None:
        self.pot.open_slots.add(slot)

    def close(self, slot: int) -> None:
        self.pot.open_slots.discard(slot)


def build_sim_machine(slots: dict[int, dict]) -> tuple[Machine, SimPot]:
    pot = SimPot(slots)
    machine = Machine(
        clock=SimClock(pot),
        heater=SimHeater(pot),
        temp=SimTempSensor(pot),
        stirrer=SimStirrer(pot),
        scale=SimScale(pot),
        dispenser=SimDispenser(pot),
    )
    return machine, pot
