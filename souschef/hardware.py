"""Hardware interfaces.

The cooking engine only talks to these abstract classes. Today they are
implemented by the simulator (simulator.py). Later, on the Raspberry Pi,
you write real versions (GPIO, relays, sensors) with the SAME methods,
and the engine code does not change at all.
"""
from abc import ABC, abstractmethod


class Clock(ABC):
    @abstractmethod
    def now(self) -> float:
        """Seconds since start."""

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Wait (the simulator just advances time instantly)."""


class Heater(ABC):
    @abstractmethod
    def set_power(self, fraction: float) -> None:
        """0.0 = off, 1.0 = full power."""


class TempSensor(ABC):
    @abstractmethod
    def read_c(self) -> float | None:
        """Pot temperature in Celsius, or None if the sensor failed."""


class Stirrer(ABC):
    @abstractmethod
    def set_rpm(self, rpm: int) -> None:
        """0 = stop."""


class Scale(ABC):
    @abstractmethod
    def read_grams(self) -> float:
        """Total weight of what is in the pot."""


class Dispenser(ABC):
    @abstractmethod
    def open(self, slot: int) -> None:
        """Start releasing the ingredient in this slot."""

    @abstractmethod
    def close(self, slot: int) -> None:
        """Stop releasing."""


class Machine:
    """Bundle of all hardware parts, handed to the engine."""

    def __init__(self, clock: Clock, heater: Heater, temp: TempSensor,
                 stirrer: Stirrer, scale: Scale, dispenser: Dispenser):
        self.clock = clock
        self.heater = heater
        self.temp = temp
        self.stirrer = stirrer
        self.scale = scale
        self.dispenser = dispenser

    def all_off(self) -> None:
        self.heater.set_power(0.0)
        self.stirrer.set_rpm(0)
