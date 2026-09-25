# A specification you can run

[![spec-check](https://github.com/filipbiernat/who-killed-the-specification/actions/workflows/spec-check.yml/badge.svg)](https://github.com/filipbiernat/who-killed-the-specification/actions/workflows/spec-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

Most specifications die the same way. Somebody writes them, everybody agrees
to them, and then the code moves on without them. Six months later the
document describes a product that no longer exists, and nobody notices,
because nothing ever checks.

This repository is a small espresso machine where that cannot happen quietly.
Seven requirements written in [EARS](#4-read-the-specification) live in
`spec/` as Markdown files. Each one names the test that verifies it. Change a
requirement's wording and the build goes red; delete a test and the build goes
red; write a sentence that no test could ever fail against and the linter says
so.

It is deliberately small enough to read in one sitting.

## Contents

1. [Prerequisites and installation](#1-prerequisites-and-installation)
2. [Run the coffee machine](#2-run-the-coffee-machine)
3. [Run the tests](#3-run-the-tests)
4. [Read the specification](#4-read-the-specification)
5. [Validate and publish the specification](#5-validate-and-publish-the-specification)
6. [Turn a requirement into code and tests](#6-turn-a-requirement-into-code-and-tests)
7. [Add your own requirement](#7-add-your-own-requirement)
8. [Break it on purpose](#8-break-it-on-purpose)
9. [Traceability](#9-traceability)
10. [Guided tour](#10-guided-tour)
11. [Asset provenance](#11-asset-provenance)
12. [License and credits](#12-license-and-credits)

## 1. Prerequisites and installation

Python 3.13 and nothing else. No database, no container, no build step.

```bash
git clone https://github.com/filipbiernat/who-killed-the-specification.git
cd who-killed-the-specification

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev,viz]"
```

Check that the specification tool is the one this project expects:

```bash
doorstop --version                 # Doorstop v3.2
```

The `viz` extra is only needed for section 2. If you only care about the
specification and the tests, `pip install -e ".[dev]"` is enough.

## 2. Run the coffee machine

```bash
uvicorn viz.server:app --port 8000
```

Open <http://localhost:8000>. The page shows three things side by side: a
requirement, the code that implements it, and the machine itself.

Press **Empty the tank**, then **Select espresso**. The machine refuses to
brew and the warning lamp comes on. That refusal is not animated in the
browser — the page asked the real `CoffeeMachine` what happened and drew the
answer. The same method the tests call is the one driving the picture.

Now edit `src/coffee_machine/brew_control.py` and save. The server reloads the
module, rebuilds the machine and pushes the new state to the page. The source
listing and its hash update in front of you.

## 3. Run the tests

```bash
pytest                             # everything
pytest -m REQ_BREW_014             # only the tests for one requirement
ptw .                              # re-run on every save
```

The middle one is the interesting one. Every test declares which requirement
it verifies:

```python
@pytest.mark.requirement("REQ-BREW-014")
def test_empty_tank_refuses_espresso():
    ...
```

`tests/conftest.py` turns each requirement ID into a marker of its own, which
is what makes `-m REQ_BREW_014` work. Hyphens become underscores because
`-m` cannot express a hyphen. The same marker writes the ID into the JUnit XML
and into `trace.json`.

## 4. Read the specification

`spec/` is one [Doorstop](https://doorstop.readthedocs.io) document. Every
requirement is a file:

```markdown
---
active: true
derived: false
level: 2.2
links: []
normative: true
ref: ''
references:
- keyword: REQ-BREW-014
  path: tests/test_brew_control.py
  type: file
reviewed: wnrc5EBXJqBfzkdx_cyQRxp3IRvY2dBdihXX06tlXgI=
risk: high
tags:
- safety
---

# Refuse to brew with an empty tank

When the user selects espresso and the water tank is empty,
the machine shall refuse to brew.

*Rationale:* dry-running the pump destroys the heating element.
```

`level:` is where the requirement sits in the published document, not what it
means. The three files whose level ends in `.0` are section headings: they are
`normative: false`, they promise nothing, and they exist so the compiled
document has chapters rather than seven equal headings in a row.

The heading is a label for humans. The requirement is the sentence beneath it,
and it is written in EARS — Easy Approach to Requirements Syntax, which has
five patterns and no sixth:

| Pattern | Shape | Example in this repository |
|---|---|---|
| ubiquitous | `The <actor> shall <behaviour>.` | `REQ-BREW-001` |
| event-driven | `When <trigger>, the <actor> shall <behaviour>.` | `REQ-BREW-014` |
| state-driven | `While <state>, the <actor> shall <behaviour>.` | `REQ-BREW-002` |
| optional feature | `Where <feature>, the <actor> shall <behaviour>.` | `REQ-BREW-007` |
| unwanted behaviour | `If <condition>, then the <actor> shall <behaviour>.` | none yet |

The last row has no example on purpose. Unwanted behaviour is for conditions
that should never arise, and this machine has nothing that can go wrong behind
its own back: refusing to brew on an empty tank is the design working, so it
is an event rather than a fault.

Three house rules are enforced rather than hoped for, and they are checked by
`tools/spec_lint.py`:

- **One `shall` per requirement.** Two `shall` clauses are two requirements
  sharing one ID, and a test written against them can only half-fail.
- **No `shall`, no requirement.** `should`, `may` and `will` describe wishes.
- **Every normative requirement names a covering test** in `references:`.

`reviewed:` is a hash of the requirement as it was last accepted. It is how
the tooling notices that the words changed after everyone agreed to them.

## 5. Validate and publish the specification

```bash
doorstop -e -F                     # validate; non-zero exit if anything drifted
python -m tools.spec_lint          # EARS and the house rules
```

Both `doorstop` flags matter, and leaving either out is a quiet mistake:

- **`-e`** promotes warnings to errors. Without it, a requirement whose text
  changed after review is reported as a *warning* and the command still exits
  **zero** — so a build gated on it would pass while the specification had
  already drifted.
- **`-F`** stops Doorstop reformatting the requirement files while it
  validates them, which otherwise leaves you with unexplained modifications in
  `git status`.

Worth knowing before you rely on that gate: it guards *changes*, not new
writing. A requirement whose `reviewed:` field is still empty gets stamped
automatically the first time validation runs. What cannot pass unnoticed is
editing a sentence everybody had already agreed to.

When a requirement's new wording is what you meant, accept it:

```bash
doorstop review all
```

Read that as agreeing to the sentence, not as clearing a red light.

To publish the specification as a browsable document:

```bash
doorstop publish all ./public --template spec
```

`--template spec` picks up `spec/template/`, which holds the layout and the
stylesheet this project publishes with. Without the flag Doorstop falls back
to its own theme, which works but arrives branded as Doorstop.

## 6. Turn a requirement into code and tests

This is the part worth trying. The requirement is the input; the code and the
tests are the output; the wording of the requirement is what determines them.

Four skills in `.cursor/skills/` carry the conventions, so the instructions
below can stay short: `spec-authoring` for the sentences, `spec-to-code` and
`spec-to-tests` for what comes out of them, and `risk-analysis` for what the
sentences do not say yet. They work in any editor that reads `AGENTS.md` and the
`.cursor/skills/` convention; without one, paste the relevant `SKILL.md`
first.

**Step one — implement it.** Paste this:

> Read `REQ-BREW-007` in `spec/` and implement it in `src/coffee_machine/`.
> Keep the requirement's own vocabulary and units, put its ID in a comment
> beside any constant you add, and do not widen the range it states.

Expect a named constant in `model.py` with `# REQ-BREW-007` beside it, and a
guard clause in `brew_control.py` returning a refusal — not a raised
exception, because the requirement says *reject*, not *crash*.

**Step two — test it.** Paste this:

> Write the pytest tests that verify `REQ-BREW-007`. Mark them with the
> requirement marker, structure them so the EARS condition is the arrange step
> and the `shall` clause is the assertion, and cover both edges of the range
> inclusively.

Expect two parametrised tests: one for the values just outside the range and
one for the boundary values themselves.

**Step three — close the loop.** Point the requirement back at its test by
adding `references:` to the file, then:

```bash
pytest -m REQ_BREW_007
doorstop -e -F                     # will report the header change
doorstop review all                # accept it
```

## 7. Add your own requirement

```bash
doorstop add REQ-BREW              # allocates the next ID and writes a stub
```

Write one sentence in one of the five patterns. Set `risk` and `tags`. Point
`references:` at the test file that will cover it. Then follow section 6 to
generate the code and the tests, and finish with `doorstop review all`.

Two details about the stub Doorstop writes, both of which will otherwise cost
you a confusing few minutes. Its `level:` makes the new requirement a child of
the previous one, such as `5.1`; these requirements are siblings, so flatten it
to the next whole number. And the `keyword:` inside `references:` is checked
literally — Doorstop verifies that the string appears in the referenced file,
which is why it has to be the requirement ID and why the test's
`@pytest.mark.requirement` marker has to spell that ID out. Get it wrong and
you get `external reference not found`, which does not explain itself.

Before you accept it, read the sentence and ask whether two engineers could
build different things from it. That question finds more defects than the
linter does.

## 8. Break it on purpose

The fastest way to see what is actually connected. Open
`spec/REQ-BREW-014.md` and change the requirement to something else:

```diff
-the machine shall refuse to brew.
+the machine shall brew a half cup.
```

Then:

```bash
doorstop -e -F
```

```
ERROR: REQ-BREW: REQ-BREW-014: unreviewed changes
```

The exit code is 1. Notice what did *not* happen: `pytest` still passes,
because the code has not changed — only the agreement about what the code
should do. That gap between the two is the thing this repository is built to
make visible.

Now ask for the code to be regenerated from the edited requirement and run
`pytest` again. It goes red, and it names the test that disagrees. Restore the
sentence with `git checkout spec/REQ-BREW-014.md` and everything returns to
green.

## 9. Traceability

Two reports, describing two different relationships. It is worth knowing which
is which:

| File | Produced by | Answers |
|---|---|---|
| `public/traceability.html` | `doorstop publish` | how requirements relate to each other |
| `public/test-coverage.html` | `python -m tools.trace_report` | which tests verify each requirement, and whether they passed |
| `public/risk-analysis.html` | `python -m tools.risk_report` | what the specification does not say yet |

The second one is generated from `trace.json`, which `pytest` writes at the
end of every run from the requirement markers. It exits non-zero if any
normative requirement has no test or has a failing one, which is why coverage
of the specification is a fact here rather than a claim.

The link is enforced from both ends: `tests/test_spec_quality.py` fails for
any normative requirement with an empty `references:`, and `trace_report`
fails for any requirement no test has claimed.

Continuous integration runs the same commands in the same order
(`.github/workflows/spec-check.yml`), plus a second workflow that asks a model
to review changed requirements for ambiguity. That reviewer comments and never
blocks — merging is gated by the deterministic checks, not by the model.

## 10. Guided tour

The full loop, in order, from a clean clone:

```bash
pip install -e ".[dev,viz]"

doorstop -e -F                          # the specification is valid
python -m tools.spec_lint               # every sentence is well formed
pytest                                  # all tests pass
python -m tools.trace_report            # every requirement is covered
python -m tools.risk_report             # what the specification still does not say

uvicorn viz.server:app --port 8000      # watch it run, then stop it

# now break the agreement
sed -i 's/shall refuse to brew/shall brew a half cup/' spec/REQ-BREW-014.md
doorstop -e -F                          # red: exit 1, unreviewed changes
pytest                                  # still green: the code is unchanged

git checkout spec/REQ-BREW-014.md       # put it back
doorstop -e -F                          # green again
```

## 11. Asset provenance

The machine illustration in `viz/static/machine.svg` is hand-written SVG: every
shape carries a stable ID such as `#water` or `#warning-light`, which is what
lets the stylesheet bind it to the machine's state.

Its geometry, proportions and palette were measured off a reference image
generated with an image model. The reference was something to draw from and
nothing more: no generated raster is shipped in the page or kept in the
repository.

## 12. License and credits

Released under the [MIT License](LICENSE).

This project stands on two ideas it did not invent. [Doorstop](https://github.com/doorstop-dev/doorstop)
by Jace Browning keeps requirements in version control as plain files, which is
what makes any of this possible. **EARS** was introduced by Alistair Mavin and
colleagues in *Easy Approach to Requirements Syntax* (RE'09); the five patterns
used here are theirs.
