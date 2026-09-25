"""Vocabulary of the coffee machine: its hardware and its display."""

from dataclasses import dataclass
from enum import Enum

# Not specified anywhere: no requirement mentions the cup on the tray. It is
# configuration, and it lives here so the drawing knows how much coffee counts
# as a full cup.
CUP_CAPACITY_ML = 75


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
