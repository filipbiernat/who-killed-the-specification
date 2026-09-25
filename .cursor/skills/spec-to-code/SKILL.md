---
name: spec-to-code
description: Turn a requirement from spec/ into an implementation in src/coffee_machine/, keeping the requirement's vocabulary, units and ranges intact and leaving the UID visible in the code. Covers where each kind of logic belongs, the module-import discipline the hot-reloading server depends on, and how to order competing refusals. Use when asked to implement a requirement, generate code for a REQ-BREW id, make the machine obey a requirement, update the code after a requirement changed, or find where a requirement is implemented.
icon: code
color: blue
---

# From a requirement to code

The requirement decides what the code must do. This skill only decides where
the code goes and what it is allowed to look like.

## Read the sentence first

Take the requirement's own words as the vocabulary of the implementation. If
the sentence says "refuse to brew", the result is a refusal, not a raised
exception or a `False` return. If it says "between 25 ml and 250 ml", both
bounds are inclusive until the sentence says otherwise, and the units are
millilitres everywhere.

Never widen or narrow a range while implementing it. If the range in the
sentence looks wrong, say so and stop; do not quietly write what you think was
meant.

## Where things belong

| Module | Responsibility |
|---|---|
| `model.py` | Vocabulary: drinks, hardware, refusal reasons, warnings, limits. |
| `brew_control.py` | The decision. Pure functions over the model, no state. |
| `machine.py` | State and the one entry point, `request_brew()`. |
| `telemetry.py` | A serialisable view of the machine for anything that draws it. |

A new limit or named value goes in `model.py` as a module-level constant with
the requirement's UID in a comment beside it:

```python
# REQ-BREW-007: the range a custom volume has to stay within.
MIN_VOLUME_ML = 25
MAX_VOLUME_ML = 250
```

New behaviour goes in `brew_control.py` as a branch in `decide()`, with the
UID in a comment above the branch. Keep `decide()` flat and readable: a chain
of guard clauses that each return a refusal, ending in the success case.

## The import rule

Inside the package, import modules and not names:

```python
from . import model          # yes
from .model import Tank      # no
```

The visualisation server calls `importlib.reload()` on these modules while it
is running. A reloaded module object is updated in place, so `model.Tank`
resolves to the new class. A name imported directly still points at the old
one, and the server then shows stale behaviour while reporting a fresh source
hash — which is a genuinely confusing thing to debug.

For the same reason, anything holding a long-lived instance has to rebuild it
after a reload rather than keep the old object.

## Keep what the visualisation reads

`viz/` is not specified and not tested, so no test notices when a
regeneration breaks it; the browser just goes blank. Whatever else changes,
keep these names and shapes:

- `machine.CoffeeMachine(tank=model.Tank(level_ml=..., capacity_ml=...))`
- on the machine: `tank`, `boiler.is_ready`, `display.warning`, `cup_ml`,
  `refill()`, and `request_brew(drink)` returning a result with `brew_started`
- `model.Drink.ESPRESSO`, `model.Warning.NONE`, `Warning.banner`,
  `model.CUP_CAPACITY_ML`
- `telemetry.snapshot(machine, state)` and the keys it returns

## Ordering competing refusals

When more than one requirement could refuse the same request, the order of the
checks is itself a decision, and it needs a reason recorded in a comment.

In this project safety outranks quality: an empty tank is reported before a
cold boiler, because running the pump dry damages the machine while brewing
cold merely tastes bad. Make the ordering explicit and cover it with a test,
so the decision cannot be reversed silently by a later edit.

## Finish the loop

Implementing a requirement is not done until the tests that cover it pass and
the specification still validates:

```bash
pytest -m REQ_BREW_014          # the requirement you just implemented
pytest                          # nothing else broke
doorstop -e -F                  # the specification itself is still clean
```

If the requirement's prose changed as part of this work, `doorstop -e -F` will
report it as unreviewed. That is correct and it is not for this skill to
clear: accepting new wording is an authoring decision.
