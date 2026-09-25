"""Wire pytest to the requirements.

Three jobs, all built on the one marker ``@pytest.mark.requirement("REQ-...")``:

1. give every requirement its own selector, so ``pytest -m REQ_BREW_014``
   runs exactly the tests for that requirement;
2. record which requirement a test verifies in the JUnit XML, so a CI
   system can read it without knowing anything about this project;
3. write ``trace.json`` and ``.demo/results.json`` when the run ends.
"""

import json
import os
from pathlib import Path

import pytest

from tools import spec_loader

ROOT = Path(__file__).resolve().parent.parent

# nodeid -> {"outcome": ..., "uids": [...]}, filled in as tests report back.
_RESULTS: dict[str, dict] = {}


def _selector(uid: str) -> str:
    """``REQ-BREW-014`` -> ``REQ_BREW_014``; ``-m`` cannot express a hyphen."""
    return uid.replace("-", "_")


def _requirements():
    """The items a test can verify.

    ``spec/`` also holds the section headings that give the published document
    its structure. They are non-normative: they promise nothing, so there is
    nothing for a test to prove and nothing to report as uncovered.
    """
    return [item for item in spec_loader.load_all() if item.normative]


def pytest_configure(config):
    """Register one marker per requirement so --strict-markers stays on."""
    for requirement in _requirements():
        config.addinivalue_line(
            "markers",
            f"{_selector(requirement.uid)}: verifies {requirement.uid}",
        )


def pytest_collection_modifyitems(items):
    """Turn the requirement IDs on each test into selectable markers."""
    for item in items:
        for marker in item.iter_markers(name="requirement"):
            for uid in marker.args:
                item.add_marker(getattr(pytest.mark, _selector(uid)))


@pytest.fixture(autouse=True)
def _record_requirement(request, record_property):
    """Put the requirement IDs into the JUnit XML for this test."""
    for marker in request.node.iter_markers(name="requirement"):
        for uid in marker.args:
            record_property("verifies", uid)


def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    uids = [value for name, value in report.user_properties if name == "verifies"]
    _RESULTS[report.nodeid] = {"outcome": report.outcome, "uids": uids}


def pytest_sessionfinish(session, exitstatus):
    trace = {
        requirement.uid: {
            "heading": requirement.heading,
            "risk": requirement.risk,
            "tests": [],
        }
        for requirement in _requirements()
    }

    passed = failed = 0
    first_failure = None
    for nodeid, result in _RESULTS.items():
        if result["outcome"] == "passed":
            passed += 1
        else:
            failed += 1
            first_failure = first_failure or nodeid.split("::")[-1]
        for uid in result["uids"]:
            if uid in trace:
                trace[uid]["tests"].append(
                    {"nodeid": nodeid, "outcome": result["outcome"]}
                )

    _write_json(ROOT / "trace.json", trace)
    _write_json(
        ROOT / ".demo" / "results.json",
        {"passed": passed, "failed": failed, "first_failure": first_failure},
    )


def _write_json(path: Path, payload) -> None:
    """Write atomically: a half-written file is worse than a stale one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)
