---
name: spec-to-tests
description: Turn a requirement from spec/ into pytest tests whose structure mirrors the requirement's grammar, with the EARS condition as the arrange step and the shall clause as the assertion. Covers the requirement marker that makes each UID selectable, what to name a test, which boundaries to cover, and how to close the loop back to the references field. Use when asked to write tests for a requirement, generate a test for a REQ-BREW id, check whether a requirement is covered, or find which test verifies a requirement.
icon: beaker
color: green
---

# From a requirement to tests

The grammar of an EARS sentence is already the skeleton of a test. Keep them
in the same shape and a reader can check one against the other without
thinking.

## Map the sentence onto the test

| In the requirement | In the test |
|---|---|
| `when` / `while` / `where` / `if` clause | arrange: build the machine in that state |
| the action the clause implies | act: one call, normally `request_brew()` |
| the `shall` clause | assert: the observable outcome |

```python
@pytest.mark.requirement("REQ-BREW-014")
def test_empty_tank_refuses_espresso():
    machine = CoffeeMachine(tank=Tank(level_ml=0))      # when the tank is empty

    result = machine.request_brew(Drink.ESPRESSO)        # the user selects espresso

    assert result.brew_started is False                  # shall refuse to brew
    assert result.refusal is Refusal.TANK_EMPTY
```

Assert the behaviour the sentence names, then the detail that identifies it.
`brew_started is False` is the requirement; the refusal reason is how the rest
of the system tells this refusal apart from another.

## The marker is not optional

Every test carries the UID of the requirement it verifies:

```python
@pytest.mark.requirement("REQ-BREW-014")
```

`tests/conftest.py` turns each UID into a marker of its own, so a single
requirement can be run in isolation:

```bash
pytest -m REQ_BREW_014
```

The selector replaces hyphens with underscores because `-m` cannot express a
hyphen. The same marker puts the UID into the JUnit XML and into
`trace.json`, which is what makes coverage of the specification measurable
rather than asserted.

A test with no marker is invisible to all of that, however good it is.

## Naming

Name the test after the behaviour, not the mechanism: 
`test_empty_tank_refuses_espresso`, not `test_decide_returns_false`. Read the
name next to the requirement heading; if they say different things, one of
them is wrong.

## What to cover

Cover the behaviour the sentence promises, then the boundary it implies:

- the stated case (`while` the boiler is cold: refuse);
- the complement, so the test can fail for the right reason (boiler ready:
  brew);
- both edges of any range, inclusive, parametrised;
- the interaction, where one requirement can mask another. If an empty tank
  outranks a cold boiler, assert that ordering explicitly.

Do not test the same thing twice through different doors, and do not test
`viz/` at all: it is a view of state, it decides nothing, and it is not
specified.

## Close the loop

A test only counts as coverage once the requirement points back at it:

```yaml
references:
- keyword: REQ-BREW-014
  path: tests/test_brew_control.py
  type: file
```

`tests/test_spec_quality.py` fails for any normative requirement with an empty
`references:` field, so the link is enforced in both directions. After adding
the field, run `doorstop -e -F`; changing the header counts as a change, so
the requirement will need `doorstop review` again.
