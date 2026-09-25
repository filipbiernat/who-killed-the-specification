"""The brew decision. Pure functions over the model, no state of their own."""

from . import model


def decide(
    request: "model.BrewRequest",
    tank: "model.Tank",
    boiler: "model.Boiler",
) -> "model.BrewResult":
    """Whether this request may start.

    REQ-BREW-014's sentence is checked first: espresso from an empty tank
    pours a half cup, and that sentence does not mention the boiler or the
    requested volume. Every other empty tank is still a refusal, and that
    refusal is reported before a short tank, a short tank before a cold
    boiler, and a cold boiler before a volume outside the range. Running
    dry damages the machine; brewing cold only tastes bad.
    """
    volume_ml = request.requested_volume_ml

    # REQ-BREW-014: espresso selected while the tank is empty pours a half cup.
    if request.drink == model.Drink.ESPRESSO and tank.is_empty:
        return model.BrewResult(brew_started=True, volume_ml=model.HALF_CUP_ML)

    # An empty tank on any other drink. REQ-BREW-021 names this refusal.
    # It stays ahead of REQ-BREW-015: empty is not the same report as short.
    if tank.is_empty:
        return model.BrewResult(brew_started=False, refusal=model.Refusal.TANK_EMPTY)

    # REQ-BREW-015: not empty is not the same as enough for the requested volume.
    if not tank.holds_at_least(volume_ml):
        return model.BrewResult(
            brew_started=False, refusal=model.Refusal.INSUFFICIENT_WATER
        )

    # REQ-BREW-002: below the target temperature, do not start brewing.
    if not boiler.is_ready:
        return model.BrewResult(brew_started=False, refusal=model.Refusal.BOILER_COLD)

    # REQ-BREW-007: a custom volume outside 25 ml to 250 ml is rejected.
    if request.rejects_custom_volume():
        return model.BrewResult(
            brew_started=False, refusal=model.Refusal.VOLUME_OUT_OF_RANGE
        )

    # REQ-BREW-001: an offered drink pours at the requested volume.
    return model.BrewResult(brew_started=True, volume_ml=volume_ml)


def warning_for(result: "model.BrewResult") -> "model.Warning":
    """The words the display shows for a decision.

    REQ-BREW-021: an empty tank shows a refill warning.
    REQ-BREW-022: every other refusal shows a warning naming that reason.
    A short tank shares the refill warning, because the tank still cannot
    supply the cup. A brew that started shows nothing.
    """
    if result.brew_started or result.refusal is None:
        return model.Warning.NONE

    shown = {
        model.Refusal.TANK_EMPTY: model.Warning.REFILL_TANK,
        model.Refusal.INSUFFICIENT_WATER: model.Warning.REFILL_TANK,
        model.Refusal.BOILER_COLD: model.Warning.WAIT_FOR_HEAT,
        model.Refusal.VOLUME_OUT_OF_RANGE: model.Warning.ADJUST_VOLUME,
    }
    return shown[result.refusal]
