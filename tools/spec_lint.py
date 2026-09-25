"""Check requirements against EARS and against this project's house rules.

EARS (Easy Approach to Requirements Syntax) has five patterns. A sentence
that matches none of them is usually a wish rather than a requirement.

Matching is deliberately case-insensitive: requirement files are written in
ordinary sentence case, while EARS textbooks and slides set the keywords in
capitals. Both have to pass.
"""

import re
import sys

from tools import spec_loader

ACTOR = r"the\s+\w[\w\s]*?"
BEHAVIOUR = r".+"

PATTERNS = {
    "event-driven": re.compile(
        rf"^when\s+.+?,\s*{ACTOR}\s+shall\s+{BEHAVIOUR}$", re.IGNORECASE | re.DOTALL
    ),
    "state-driven": re.compile(
        rf"^while\s+.+?,\s*{ACTOR}\s+shall\s+{BEHAVIOUR}$", re.IGNORECASE | re.DOTALL
    ),
    "optional-feature": re.compile(
        rf"^where\s+.+?,\s*{ACTOR}\s+shall\s+{BEHAVIOUR}$", re.IGNORECASE | re.DOTALL
    ),
    "unwanted-behaviour": re.compile(
        rf"^if\s+.+?,\s*then\s+{ACTOR}\s+shall\s+{BEHAVIOUR}$",
        re.IGNORECASE | re.DOTALL,
    ),
    "ubiquitous": re.compile(
        rf"^{ACTOR}\s+shall\s+{BEHAVIOUR}$", re.IGNORECASE | re.DOTALL
    ),
}

# "unwanted-behaviour" has to be tried before "event-driven" would ever see
# it, and "ubiquitous" last, because it is the most permissive.
PATTERN_ORDER = (
    "event-driven",
    "state-driven",
    "optional-feature",
    "unwanted-behaviour",
    "ubiquitous",
)


def classify(text: str) -> str | None:
    """Return the name of the EARS pattern this sentence follows."""
    normalised = " ".join(text.split())
    for name in PATTERN_ORDER:
        if PATTERNS[name].match(normalised):
            return name
    return None


def check(requirement) -> list[str]:
    """Return a list of problems. An empty list means the requirement is fine."""
    problems = []
    if not requirement.normative:
        return problems

    shall_clauses = len(re.findall(r"\bshall\b", requirement.text, re.IGNORECASE))
    if shall_clauses == 0:
        problems.append(
            "no 'shall': this is not a requirement yet, it is a wish"
        )
    elif shall_clauses > 1:
        problems.append(
            f"{shall_clauses} 'shall' clauses: this is {shall_clauses} "
            "requirements sharing one UID, and a test written against it "
            "can only half-fail"
        )
    elif classify(requirement.text) is None:
        problems.append(
            "does not match any EARS pattern "
            "(ubiquitous / when / while / where / if-then)"
        )

    if not requirement.references:
        problems.append(
            "no 'references:' entry, so nothing proves a test covers it"
        )
    return problems


def main() -> int:
    failures = 0
    for requirement in spec_loader.load_all():
        problems = check(requirement)
        if problems:
            failures += 1
            for problem in problems:
                print(f"{requirement.uid}: {problem}")
        elif not requirement.normative:
            print(f"{requirement.uid}: section heading, nothing to promise")
        else:
            print(f"{requirement.uid}: ok ({classify(requirement.text)})")
    if failures:
        print(f"\n{failures} requirement(s) need work")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
