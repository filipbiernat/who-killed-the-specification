"""A serialisable view of the machine, for anything that wants to draw it.

The browser renders this and nothing else. Every number it needs comes from
here, so the front end never has to know a capacity or a threshold of its own.
"""


from . import model


def snapshot(machine, state: str = "idle") -> dict:
    return {
        "state": state,
        "tank_ml": machine.tank.level_ml,
        "tank_capacity_ml": machine.tank.capacity_ml,
        "cup_ml": machine.cup_ml,
        "cup_capacity_ml": model.CUP_CAPACITY_ML,
        "boiler_ready": machine.boiler.is_ready,
        "warning": machine.display.warning.value,
        "warning_banner": machine.display.warning.banner,
    }
