"""Behavioural tests. Each one names the requirement it verifies.

The shape of every test follows the shape of the requirement sentence:
the ``when``/``while``/``where``/``if`` clause is the arrange step, the
action is the act step, and the ``shall`` clause is the assertion.
"""

import pytest

from coffee_machine import brew_control
from coffee_machine.machine import CoffeeMachine
from coffee_machine.model import Boiler, BrewResult, Drink, Refusal, Tank, Warning


@pytest.mark.requirement("REQ-BREW-001")
def test_offers_the_three_standard_drinks():
    assert {drink.name for drink in Drink} == {"ESPRESSO", "LUNGO", "AMERICANO"}


@pytest.mark.requirement("REQ-BREW-001")
@pytest.mark.parametrize("drink", list(Drink))
def test_every_offered_drink_can_actually_be_brewed(drink):
    """Naming a drink is not offering it; the machine has to pour it."""
    machine = CoffeeMachine()

    result = machine.request_brew(drink)

    assert result.brew_started is True
    assert result.volume_ml == drink.default_volume_ml


@pytest.mark.requirement("REQ-BREW-002")
def test_cold_boiler_refuses_to_start_brewing():
    machine = CoffeeMachine(boiler=Boiler(temperature_c=40, target_c=90))

    result = machine.request_brew(Drink.ESPRESSO)

    assert result.brew_started is False
    assert result.refusal is Refusal.BOILER_COLD


@pytest.mark.requirement("REQ-BREW-002")
def test_ready_boiler_allows_brewing():
    machine = CoffeeMachine(boiler=Boiler(temperature_c=93, target_c=90))

    result = machine.request_brew(Drink.ESPRESSO)

    assert result.brew_started is True


@pytest.mark.requirement("REQ-BREW-002")
def test_boiler_exactly_at_target_is_warm_enough():
    """'below its target' excludes the target itself, so 90 == 90 brews."""
    machine = CoffeeMachine(boiler=Boiler(temperature_c=90, target_c=90))

    result = machine.request_brew(Drink.ESPRESSO)

    assert result.brew_started is True


@pytest.mark.requirement("REQ-BREW-007")
@pytest.mark.parametrize("volume_ml", [24, 251])
def test_custom_volume_outside_the_range_is_rejected(volume_ml):
    machine = CoffeeMachine()

    result = machine.request_brew(Drink.ESPRESSO, volume_ml=volume_ml)

    assert result.brew_started is False
    assert result.refusal is Refusal.VOLUME_OUT_OF_RANGE


@pytest.mark.requirement("REQ-BREW-007")
@pytest.mark.parametrize("volume_ml", [25, 250])
def test_custom_volume_on_the_boundary_is_accepted(volume_ml):
    machine = CoffeeMachine()

    result = machine.request_brew(Drink.ESPRESSO, volume_ml=volume_ml)

    assert result.brew_started is True
    assert result.volume_ml == volume_ml


@pytest.mark.requirement("REQ-BREW-014")
def test_empty_tank_refuses_espresso():
    # ARRANGE: "and the water tank is empty"
    machine = CoffeeMachine(tank=Tank(level_ml=0))

    # ACT: "When the user selects espresso"
    result = machine.request_brew(Drink.ESPRESSO)

    # ASSERT: "the machine shall refuse to brew"
    assert result.brew_started is False
    assert result.refusal is Refusal.TANK_EMPTY


@pytest.mark.requirement("REQ-BREW-014")
def test_empty_tank_outranks_a_cold_boiler():
    """An empty tank is a safety matter, so it is reported first."""
    machine = CoffeeMachine(
        tank=Tank(level_ml=0), boiler=Boiler(temperature_c=40, target_c=90)
    )

    result = machine.request_brew(Drink.ESPRESSO)

    assert result.refusal is Refusal.TANK_EMPTY


@pytest.mark.requirement("REQ-BREW-015")
def test_a_tank_below_the_cup_size_refuses_to_brew():
    # ARRANGE: "and the water tank holds less water than the requested volume"
    machine = CoffeeMachine(tank=Tank(level_ml=20))

    # ACT: "When the user requests a brew"
    result = machine.request_brew(Drink.ESPRESSO)

    # ASSERT: "the machine shall refuse to brew"
    assert result.brew_started is False
    assert result.refusal is Refusal.INSUFFICIENT_WATER


@pytest.mark.requirement("REQ-BREW-015")
def test_a_tank_holding_exactly_the_cup_size_brews():
    """'less water than the requested volume' excludes exactly enough."""
    machine = CoffeeMachine(tank=Tank(level_ml=Drink.ESPRESSO.default_volume_ml))

    result = machine.request_brew(Drink.ESPRESSO)

    assert result.brew_started is True


@pytest.mark.requirement("REQ-BREW-021")
def test_refusing_on_an_empty_tank_shows_the_refill_warning():
    # ARRANGE: "because the water tank is empty"
    machine = CoffeeMachine(tank=Tank(level_ml=0))

    # ACT: "When the machine refuses to brew"
    machine.request_brew(Drink.ESPRESSO)

    # ASSERT: "the machine shall show a refill warning on its display"
    assert machine.display.warning is Warning.REFILL_TANK


@pytest.mark.requirement("REQ-BREW-021")
def test_a_successful_brew_shows_no_warning():
    machine = CoffeeMachine()

    machine.request_brew(Drink.ESPRESSO)

    assert machine.display.warning is Warning.NONE


@pytest.mark.requirement("REQ-BREW-022")
def test_a_cold_boiler_says_so_on_the_display():
    machine = CoffeeMachine(boiler=Boiler(temperature_c=40, target_c=90))

    machine.request_brew(Drink.ESPRESSO)

    assert machine.display.warning is Warning.WAIT_FOR_HEAT


@pytest.mark.requirement("REQ-BREW-022")
def test_a_rejected_volume_says_so_on_the_display():
    machine = CoffeeMachine()

    machine.request_brew(Drink.ESPRESSO, volume_ml=251)

    assert machine.display.warning is Warning.ADJUST_VOLUME


@pytest.mark.requirement("REQ-BREW-022")
def test_too_little_water_asks_for_a_refill():
    machine = CoffeeMachine(tank=Tank(level_ml=20))

    machine.request_brew(Drink.ESPRESSO)

    assert machine.display.warning is Warning.REFILL_TANK


@pytest.mark.requirement("REQ-BREW-022")
def test_no_refusal_reason_is_left_without_a_warning():
    """The requirement says every refusal; nothing may map to silence."""
    silent = [
        refusal
        for refusal in Refusal
        if brew_control.warning_for(BrewResult(brew_started=False, refusal=refusal))
        is Warning.NONE
    ]

    assert silent == []
