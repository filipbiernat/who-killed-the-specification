"""Derive an FMEA-style risk analysis from the specification and the code.

There is no AI here. Every row below is read out of ``spec/`` or out of the
model itself, which is the only reason it can be trusted: an analysis that
invents a descaling cycle the machine does not have is worse than no analysis.

The six headings are the usual ones. What each means here:

* inputs        every value the brew decision reads
* outputs       everything it can produce
* noise factors numbers the behaviour depends on that no requirement fixes
* failure modes gaps between what is agreed and what the code does
* mitigations   the gates that exist, and what each one would catch
* corner cases  the boundaries those numbers imply

This is a draft to argue with, not a verdict, so it never fails the build.
"""

import dataclasses
import inspect
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from coffee_machine import brew_control, machine as machine_module, model  # noqa: E402

from tools import spec_loader  # noqa: E402

OUTPUT_FILE = ROOT / "public" / "risk-analysis.html"
CORE_MODULES = (model, brew_control, machine_module)
UID_PATTERN = re.compile(r"REQ-[A-Z]+-\d+")


def numbers_in_the_model() -> list[tuple[str, int]]:
    """Every integer the behaviour depends on, with where it is written."""
    found: list[tuple[str, int]] = []

    for name, value in vars(model).items():
        if name.isupper() and isinstance(value, int):
            found.append((f"model.{name}", value))

    for drink in model.Drink:
        found.append((f"Drink.{drink.name}.default_volume_ml", drink.value))

    for cls in (model.Tank, model.Boiler):
        for field in dataclasses.fields(cls):
            if isinstance(field.default, int) and not isinstance(field.default, bool):
                found.append((f"{cls.__name__}.{field.name}", field.default))

    return found


def inputs(requirements) -> list[tuple[str, str]]:
    """The parameters of the brew decision, expanded into their fields."""
    rows = []
    for name, parameter in inspect.signature(brew_control.decide).parameters.items():
        annotation = str(parameter.annotation).strip("'\"").replace("model.", "")
        cls = getattr(model, annotation, None)
        if cls is not None and dataclasses.is_dataclass(cls):
            fields = ", ".join(field.name for field in dataclasses.fields(cls))
        else:
            fields = "-"
        rows.append((f"{name}: {annotation}", fields))
    return rows


def outputs() -> list[tuple[str, str]]:
    result_fields = ", ".join(field.name for field in dataclasses.fields(model.BrewResult))
    return [
        ("BrewResult", result_fields),
        ("Refusal", ", ".join(member.name for member in model.Refusal)),
        ("Warning", ", ".join(member.name for member in model.Warning)),
    ]


def governed_numbers(requirements) -> set[int]:
    """Numbers a requirement actually writes down.

    Only normative text counts. A section heading is prose about the document,
    not a promise about the machine, so a number that appears in one governs
    nothing and must not quietly excuse a constant from the noise list.
    """
    prose = " ".join(item.text for item in requirements if item.normative)
    return {int(match) for match in re.findall(r"\d+", prose)}


def noise_factors(requirements) -> list[tuple[str, int]]:
    agreed = governed_numbers(requirements)
    return [(where, value) for where, value in numbers_in_the_model() if value not in agreed]


def implemented_uids() -> set[str]:
    """Requirement identifiers named in a comment or docstring in src/."""
    uids: set[str] = set()
    for path in (ROOT / "src").rglob("*.py"):
        uids.update(UID_PATTERN.findall(path.read_text(encoding="utf-8")))
    return uids


def ungoverned_behaviour() -> list[str]:
    """Callables in the specified core that name no requirement at all."""
    loose = []
    for module in (brew_control, machine_module):
        for name, function in vars(module).items():
            if name.startswith("_") or not inspect.isfunction(function):
                continue
            if not UID_PATTERN.search(inspect.getsource(function)):
                loose.append(f"{module.__name__.split('.')[-1]}.{name}()")

    for name, method in vars(machine_module.CoffeeMachine).items():
        if name.startswith("_") or not inspect.isfunction(method):
            continue
        if not UID_PATTERN.search(inspect.getsource(method)):
            loose.append(f"CoffeeMachine.{name}()")

    return sorted(loose)


def silent_refusals() -> list[str]:
    """Any refusal the display would not name."""
    return [
        refusal.name
        for refusal in model.Refusal
        if brew_control.warning_for(
            model.BrewResult(brew_started=False, refusal=refusal)
        )
        is model.Warning.NONE
    ]


def failure_modes(requirements) -> list[tuple[str, str, str]]:
    """(what could go wrong, evidence, which gate would catch it)."""
    modes = []

    for where, value in noise_factors(requirements):
        modes.append(
            (
                "A number nothing agreed on can be changed without objection",
                f"{where} = {value}",
                "none",
            )
        )

    for callable_name in ungoverned_behaviour():
        modes.append(
            (
                "Behaviour with no requirement behind it",
                callable_name,
                "none - trace_report audits requirements without tests, "
                "never code without requirements",
            )
        )

    promised = {r.uid for r in requirements if r.normative}
    for uid in sorted(promised - implemented_uids()):
        modes.append(
            ("A requirement no source file claims to implement", uid, "pytest, trace_report")
        )

    for refusal in silent_refusals():
        modes.append(
            ("A refusal the user is never told about", f"Refusal.{refusal}", "none")
        )

    return modes


def mitigations() -> list[tuple[str, str]]:
    """The gates this repository actually has, if they are still there."""
    candidates = [
        ("spec/.doorstop.yml", "doorstop -e -F: prose edited after review fails the build"),
        ("tools/spec_lint.py", "one shall, an EARS pattern, and a named test per requirement"),
        ("tools/trace_report.py", "every normative requirement has a test, and it passes"),
        ("tests/test_spec_quality.py", "the linter's own rules are themselves tested"),
        (".github/workflows/spec-check.yml", "all of the above, on every push"),
        (".github/workflows/ai-review.yml", "a second reader on every changed requirement"),
    ]
    return [(path, what) for path, what in candidates if (ROOT / path).exists()]


def corner_cases(requirements) -> list[tuple[str, int, bool]]:
    """Each number and its neighbours, with whether the tests name it.

    A value a test reaches symbolically reads as absent here. That is the
    point of calling this a draft.
    """
    named = " ".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "tests").glob("*.py")
    )
    literals = set(re.findall(r"\d+", named))

    rows = []
    for where, value in numbers_in_the_model():
        for candidate in (value - 1, value, value + 1):
            rows.append((where, candidate, str(candidate) in literals))
    return rows


def as_text(cell) -> str:
    if isinstance(cell, bool):
        return "yes" if cell else "no"
    return str(cell)


def as_html(cell) -> str:
    if isinstance(cell, bool):
        return f"<span class='{'yes' if cell else 'no'}'>{as_text(cell)}</span>"
    return str(cell)


def print_table(title: str, header, rows) -> None:
    """The terminal gets the whole analysis, not a summary of it."""
    print(f"\n{title.upper()}")
    if not rows:
        print("  nothing found")
        return

    columns = [[as_text(cell) for cell in row] for row in rows]
    widths = [
        max(len(name), *(len(row[index]) for row in columns))
        for index, name in enumerate(header)
    ]
    for index, row in enumerate([list(header)] + columns):
        cells = (value.ljust(width) for value, width in zip(row, widths))
        line = "  " + "  ".join(cells)
        print(line.rstrip())
        if index == 0:
            print("  " + "  ".join("-" * width for width in widths))


def render(sections: dict) -> str:
    blocks = []
    for title, note, header, rows in sections["tables"]:
        head = "".join(f"<th>{column}</th>" for column in header)
        body = "".join(
            "<tr>" + "".join(f"<td>{as_html(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        ) or f"<tr><td colspan='{len(header)}' class='none'>nothing found</td></tr>"
        blocks.append(
            f"<h2>{title}</h2><p class='note'>{note}</p>"
            f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Risk analysis</title>
<style>
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 40px auto;
          max-width: 1000px; color: #2B2B2B; }}
  h1 {{ font-size: 24px; }}
  h2 {{ font-size: 15px; letter-spacing: .14em; text-transform: uppercase;
        color: #6E6A62; margin-top: 40px; }}
  p.lead, p.note {{ color: #6E6A62; }}
  p.note {{ font-size: 14px; margin: 0 0 12px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid #DDD;
            vertical-align: top; font-size: 14px; }}
  th {{ font-size: 11px; letter-spacing: .12em; text-transform: uppercase;
        color: #6E6A62; }}
  td.none {{ color: #2E7D4F; }}
  .no {{ color: #C0392B; font-weight: 700; }}
  .yes {{ color: #2E7D4F; font-weight: 700; }}
</style>
</head>
<body>
<h1>Risk analysis</h1>
<p class="lead">Derived from <code>spec/</code> and <code>src/coffee_machine/</code>
by <code>python -m tools.risk_report</code>. A draft to argue with, not a verdict.</p>
{"".join(blocks)}
</body>
</html>
"""


def main() -> int:
    requirements = spec_loader.load_all()

    tables = [
        ("Inputs", "Everything the brew decision reads.",
         ("parameter", "fields"), inputs(requirements)),
        ("Outputs", "Everything it can produce.",
         ("type", "members"), outputs()),
        ("Noise factors",
         "Numbers the behaviour depends on that no requirement writes down.",
         ("where", "value"), noise_factors(requirements)),
        ("Failure modes", "Gaps between what was agreed and what the code does.",
         ("what could go wrong", "evidence", "what would catch it"),
         failure_modes(requirements)),
        ("Mitigations", "The gates this repository has today.",
         ("gate", "what it catches"), mitigations()),
        ("Corner cases",
         "Each number and its neighbours. A value reached symbolically reads "
         "as absent, so treat this as a list to argue with.",
         ("boundary of", "value", "literal appears in tests/"),
         corner_cases(requirements)),
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_FILE.with_suffix(".html.tmp")
    temporary.write_text(render({"tables": tables}), encoding="utf-8")
    os.replace(temporary, OUTPUT_FILE)

    for title, _, header, rows in tables:
        print_table(title, header, rows)

    print(f"\nwritten to {OUTPUT_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
