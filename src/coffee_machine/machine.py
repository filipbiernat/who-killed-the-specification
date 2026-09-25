"""The machine itself: hardware state plus the one entry point that uses it."""

from . import brew_control
from . import model


class CoffeeMachine:
    def __init__(
        self,
        tank: "model.Tank | None" = None,
        boiler: "model.Boiler | None" = None,
    ) -> None:
        self.tank = tank if tank is not None else model.Tank()
        self.boiler = boiler if boiler is not None else model.Boiler()
        self.display = model.Display()
        self.cup_ml = 0

    def request_brew(
        self, drink: "model.Drink", volume_ml: int | None = None
    ) -> "model.BrewResult":
        """The single call shared by the tests and the visualisation server.

        REQ-BREW-021 and REQ-BREW-022: whatever the decision was, the display
        is set from it here, so no refusal can leave without a warning.
        """
        request = model.BrewRequest(drink=drink, volume_ml=volume_ml)
        result = brew_control.decide(request, self.tank, self.boiler)
        self.display.warning = brew_control.warning_for(result)

        if result.brew_started:
            # The pump can only move the water the tank holds. A brew started
            # on an empty tank runs the pump dry and pours nothing.
            poured_ml = min(result.volume_ml, self.tank.level_ml)
            self.tank.level_ml -= poured_ml
            self.cup_ml = poured_ml
        return result

    def refill(self) -> None:
        self.tank.level_ml = self.tank.capacity_ml
        self.display.warning = model.Warning.NONE
