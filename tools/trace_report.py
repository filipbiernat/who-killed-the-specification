"""Join the requirements to the test results and say what is covered.

Reads ``trace.json``, which pytest writes at the end of a run, and turns it
into a page that answers one question per requirement: is there a test, and
did it pass?

Doorstop publishes its own ``traceability.html`` describing links between
requirements. This is a different report about a different relationship, so it
is written to a different file.
"""

import json
import os
import sys
from pathlib import Path

from tools import spec_loader

ROOT = Path(__file__).resolve().parent.parent
TRACE_FILE = ROOT / "trace.json"
OUTPUT_FILE = ROOT / "public" / "test-coverage.html"


def load_trace() -> dict:
    try:
        return json.loads(TRACE_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{TRACE_FILE.name} not found; run pytest first", file=sys.stderr)
        raise SystemExit(2)


def status_of(entry: dict) -> str:
    """One word for a requirement: failing, covered, or uncovered."""
    tests = entry.get("tests", [])
    if not tests:
        return "uncovered"
    if any(test["outcome"] != "passed" for test in tests):
        return "failing"
    return "covered"


def render(rows: list[tuple]) -> str:
    cells = []
    for uid, heading, risk, status, tests in rows:
        listed = "".join(
            f"<li class='{test['outcome']}'>{test['nodeid'].split('::')[-1]}</li>"
            for test in tests
        ) or "<li class='none'>no test references this requirement</li>"
        cells.append(
            f"<tr class='{status}'>"
            f"<td class='uid'>{uid}</td>"
            f"<td>{heading}</td>"
            f"<td>{risk}</td>"
            f"<td class='status'>{status}</td>"
            f"<td><ul>{listed}</ul></td>"
            f"</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Specification coverage</title>
<style>
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 40px auto;
          max-width: 1000px; color: #2B2B2B; }}
  h1 {{ font-size: 24px; }}
  p.lead {{ color: #6E6A62; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 24px; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #DDD;
            vertical-align: top; }}
  th {{ font-size: 12px; letter-spacing: .12em; text-transform: uppercase;
        color: #6E6A62; }}
  td.uid {{ font-family: Consolas, monospace; white-space: nowrap; }}
  td.status {{ font-weight: 700; text-transform: uppercase; font-size: 12px; }}
  tr.covered td.status {{ color: #2E7D4F; }}
  tr.failing td.status, tr.uncovered td.status {{ color: #C0392B; }}
  tr.failing, tr.uncovered {{ background: #FBE9E7; }}
  ul {{ margin: 0; padding-left: 18px; }}
  li {{ font-family: Consolas, monospace; font-size: 13px; }}
  li.failed, li.none {{ color: #C0392B; }}
</style>
</head>
<body>
<h1>Specification coverage</h1>
<p class="lead">Every requirement in <code>spec/</code>, and the tests that
verify it. Generated from <code>trace.json</code>.</p>
<table>
<thead><tr><th>Requirement</th><th>Heading</th><th>Risk</th><th>Status</th>
<th>Tests</th></tr></thead>
<tbody>
{"".join(cells)}
</tbody>
</table>
</body>
</html>
"""


def main() -> int:
    trace = load_trace()
    requirements = {r.uid: r for r in spec_loader.load_all()}

    rows = []
    uncovered = []
    failing = []
    for uid, entry in sorted(trace.items()):
        status = status_of(entry)
        rows.append(
            (uid, entry.get("heading", ""), entry.get("risk", ""), status,
             entry.get("tests", []))
        )
        requirement = requirements.get(uid)
        if requirement is not None and not requirement.normative:
            continue
        if status == "uncovered":
            uncovered.append(uid)
        elif status == "failing":
            failing.append(uid)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_FILE.with_suffix(".html.tmp")
    temporary.write_text(render(rows), encoding="utf-8")
    os.replace(temporary, OUTPUT_FILE)

    print(f"{len(rows)} requirement(s) reported in {OUTPUT_FILE.name}")
    for uid in uncovered:
        print(f"{uid}: no test verifies this requirement")
    for uid in failing:
        print(f"{uid}: a test verifying this requirement failed")

    return 1 if uncovered or failing else 0


if __name__ == "__main__":
    sys.exit(main())
