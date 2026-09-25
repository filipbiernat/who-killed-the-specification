"""Vocabulary of the coffee machine: drinks, refusals, hardware and the display."""

from dataclasses import dataclass
from enum import Enum

# Not specified anywhere: no requirement mentions the cup on the tray. It is
# configuration, and it lives here so the drawing knows how much coffee counts
# as a full cup.
CUP_CAPACITY_ML = 75

# REQ-BREW-007: the range a custom volume has to stay within.
MIN_VOLUME_ML = 25
MAX_VOLUME_ML = 250


class Drink(Enum):
    """REQ-BREW-001: espresso, lungo and americano.

    The default volumes are configuration. No requirement fixes them, so a
    brew reads them from here and from nowhere else.
    """

    ESPRESSO = 30
    LUNGO = 110
    AMERICANO = 180

    @property
    def default_volume_ml(self) -> int:
        return self.value


class Refusal(Enum):
    """Why a brew did not start."""

    TANK_EMPTY = "tank_empty"  # REQ-BREW-021
    INSUFFICIENT_WATER = "insufficient_water"  # REQ-BREW-015
    BOILER_COLD = "boiler_cold"  # REQ-BREW-002
    VOLUME_OUT_OF_RANGE = "volume_out_of_range"  # REQ-BREW-007


@dataclass
class BrewRequest:
    """A brew the user asked for.

    ``volume_ml`` is a custom volume. Left unset, the drink's own default
    is what gets poured. A custom volume is valid only from ``MIN_VOLUME_ML``
    to ``MAX_VOLUME_ML``, both ends included.
    """

    drink: Drink
    volume_ml: int | None = None

    @property
    def requested_volume_ml(self) -> int:
        if self.volume_ml is None:
            return self.drink.default_volume_ml
        return self.volume_ml

    def rejects_custom_volume(self) -> bool:
        """REQ-BREW-007: below 25 ml or above 250 ml."""
        if self.volume_ml is None:
            return False
        return not MIN_VOLUME_ML <= self.volume_ml <= MAX_VOLUME_ML


@dataclass
class BrewResult:
    brew_started: bool
    volume_ml: int = 0
    refusal: Refusal | None = None


class Warning(Enum):
    """What the machine shows on its own display."""

    NONE = "none"
    REFILL_TANK = "refill_tank"
    WAIT_FOR_HEAT = "wait_for_heat"
    ADJUST_VOLUME = "adjust_volume"

    @property
    def banner(self) -> str:
        """The words on the display. Written here once, never in the browser."""
        if self is Warning.NONE:
            return ""
        return self.value.replace("_", " ").upper()


@dataclass
class Tank:
    level_ml: int = 500
    capacity_ml: int = 500

    @property
    def is_empty(self) -> bool:
        return self.level_ml <= 0

    def holds_at_least(self, volume_ml: int) -> bool:
        """REQ-BREW-015: not empty is not the same as enough."""
        return self.level_ml >= volume_ml


@dataclass
class Boiler:
    temperature_c: int = 93
    target_c: int = 90

    @property
    def is_ready(self) -> bool:
        return self.temperature_c >= self.target_c


@dataclass
class Display:
    warning: Warning = Warning.NONE
