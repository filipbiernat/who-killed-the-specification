"""Tests that read the requirements themselves.

These do not exercise the coffee machine at all. They open the Markdown
files in ``spec/`` and check the sentences: that each one follows an EARS
pattern, says ``shall``, and points at the test that covers it.
"""

import pytest

from tools import spec_lint, spec_loader

REQUIREMENTS = spec_loader.load_all()
NORMATIVE = [requirement for requirement in REQUIREMENTS if requirement.normative]


def _ids(requirements):
    return [requirement.uid for requirement in requirements]


def test_the_specification_is_not_empty():
    assert REQUIREMENTS, "no requirements found in spec/"


@pytest.mark.parametrize("requirement", NORMATIVE, ids=_ids(NORMATIVE))
def test_requirement_says_shall_exactly_once(requirement):
    """No shall and it is a wish; two and it is two requirements in a trenchcoat."""
    assert requirement.text.lower().count("shall") == 1, requirement.text


@pytest.mark.parametrize("requirement", NORMATIVE, ids=_ids(NORMATIVE))
def test_requirement_follows_an_ears_pattern(requirement):
    pattern = spec_lint.classify(requirement.text)
    assert pattern is not None, f"{requirement.uid} matches no EARS pattern: {requirement.text}"


@pytest.mark.parametrize("requirement", NORMATIVE, ids=_ids(NORMATIVE))
def test_requirement_points_at_a_test(requirement):
    """Every normative requirement has to name the file that covers it."""
    assert requirement.references, (
        f"{requirement.uid} has no 'references:' entry, "
        "so nothing proves a test covers it"
    )


def _synthetic(text: str) -> spec_loader.Requirement:
    return spec_loader.Requirement(
        uid="REQ-BREW-000",
        heading="synthetic",
        text=text,
        references=[{"path": "tests/test_brew_control.py"}],
    )


def test_the_linter_rejects_two_shall_clauses():
    """The one-shall rule is claimed to be enforced, so prove that it is.

    The sentence below is a well-formed event-driven requirement in every
    other respect, which is exactly why counting matters: the pattern match
    alone waves it through.
    """
    problems = spec_lint.check(
        _synthetic(
            "When the tank is empty, the machine shall refuse to brew "
            "and shall show a refill warning."
        )
    )

    assert any("2 'shall' clauses" in problem for problem in problems), problems


def test_the_linter_reads_a_keyword_in_any_case():
    """The files use sentence case; EARS textbooks and slides use capitals.

    Both spellings mean the same requirement, so the classifier has to accept
    either. Without this the house style would quietly become a trap for
    anyone who copied a sentence off a slide.
    """
    assert spec_lint.classify(
        "When the tank is empty, the machine shall refuse to brew."
    ) == "event-driven"
    assert spec_lint.classify(
        "WHEN the tank is empty, the machine SHALL refuse to brew."
    ) == "event-driven"


def test_the_linter_rejects_a_wish():
    problems = spec_lint.check(
        _synthetic("The machine should probably warn the user somehow.")
    )

    assert any("it is a wish" in problem for problem in problems), problems
