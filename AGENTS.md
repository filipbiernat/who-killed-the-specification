# Working in this repository

The requirements in `spec/` are the source of truth. The code exists to satisfy
them and the tests exist to prove it. Any change to behaviour starts by reading
the sentence that governs it, and if that sentence is wrong, the sentence is
what gets fixed first.

## Language

Everything committed here is in English: requirement text, identifiers,
comments, docstrings, commit messages. No exceptions.

## Layout

| Path | What lives there |
|---|---|
| `spec/` | One Doorstop document, prefix `REQ-BREW`. One requirement per file. |
| `spec/template/` | The layout and stylesheet the document publishes with. |
| `src/coffee_machine/` | The behaviour the requirements describe. |
| `tests/` | One or more tests per requirement, linked by a marker. |
| `tools/` | Reading, linting and reporting on the specification. |
| `viz/` | A browser view of the running machine. Not specified, not tested. |

## What a requirement looks like

A requirement is a Markdown file with a YAML header. The header carries the
metadata Doorstop needs; the body carries one sentence in EARS, optionally
followed by a rationale.

Three files in `spec/` are not requirements. `REQ-BREW-100`, `-200` and `-300`
are `normative: false` section headings that give the published document its
chapters, and `level:` is what puts a requirement under one of them: `1.x` for
the drink catalogue, `2.x` for the refusals, `3.x` for what reaches the
display. They promise nothing, so no test covers them and `spec_lint` passes
over them.

EARS has five patterns, and every requirement here uses exactly one of them:

| Pattern | Shape |
|---|---|
| ubiquitous | `The <actor> shall <behaviour>.` |
| event-driven | `When <trigger>, the <actor> shall <behaviour>.` |
| state-driven | `While <state>, the <actor> shall <behaviour>.` |
| optional feature | `Where <feature>, the <actor> shall <behaviour>.` |
| unwanted behaviour | `If <condition>, then the <actor> shall <behaviour>.` |

Requirements are written as ordinary sentences: the keyword that opens one is
capitalised because it starts a sentence, and `shall` stays lowercase because
it does not. EARS textbooks and conference slides set the keywords in capitals
to make the pattern visible; `tools/spec_lint.py` matches case-insensitively so
that both spellings pass and neither has to win.

Nothing in `spec/` currently uses the unwanted-behaviour pattern. It is for
conditions that should not arise at all, and this machine has no faults to
detect: refusing to brew on an empty tank is behaviour working as intended,
which makes it an event.

## House rules

1. **One `shall` per requirement.** A sentence with two `shall` clauses is two
   requirements wearing one UID, and the test that covers it can only ever
   half-fail.
2. **No `shall`, no requirement.** A sentence without it is a wish. `should`,
   `may` and `will` are not substitutes.
3. **Every normative requirement names a covering test** in its `references:`
   field. Without it there is nothing to prove the requirement is met.
4. **Requirements describe behaviour, not implementation.** Capacities and
   thresholds that are configuration rather than behaviour belong in the code.
5. **State a constant once.** If a number appears in a requirement, the code
   reads it from one place and the front end reads it from the telemetry.
   Never retype it in CSS or JavaScript.

## Code conventions

Inside `src/coffee_machine/`, import modules rather than names: write
`from . import model` and reach for `model.Tank`, not `from .model import Tank`.
The visualisation server reloads these modules while it runs, and a directly
imported name keeps pointing at the previous version of the code.

Where a constant, method or enum member exists to satisfy a requirement, name
the requirement in a comment next to it. That comment is the only place the
link is visible when reading the code alone.

## Commits

A subject line in the imperative mood, under 72 characters, no trailing period.
A body that explains why the change was needed and what is easy to get wrong
about it, wrapped at 76 characters. Describe the change, not the process that
produced it: no tool names, no co-author trailers, no references to how the
work was carried out.

## Commands

Run them from the project virtualenv: `source .venv/Scripts/activate` in Git
Bash on Windows, `source .venv/bin/activate` elsewhere. The agent shell does
not activate it on its own, and a doorstop found elsewhere on the PATH may be a
different version that validates and publishes differently.

```bash
doorstop -e -F                  # validate the specification; non-zero on drift
doorstop review all             # accept the current wording of every requirement
python -m tools.spec_lint       # check EARS and the house rules
pytest                          # run everything
pytest -m REQ_BREW_014          # run one requirement's tests
python -m tools.trace_report    # fail if a requirement has no passing test
python -m tools.risk_report     # an FMEA-style draft derived from spec/ and src/
doorstop publish all ./public --template spec   # compile the document
```

`--template spec` is not optional. It selects `spec/template/`, which holds
the layout this project publishes with; drop the flag and Doorstop falls back
to its own theme, which works but arrives branded as Doorstop.

`risk_report` is the only one of these that is not a gate. It always exits
zero, because it produces an argument to have, not a verdict: the numbers no
requirement fixes, the behaviour no requirement claims, the boundaries those
numbers imply. Nothing in it is generated by a model.

Asked for a risk analysis, an FMEA or failure modes, run that command before
saying anything: the `risk-analysis` skill exists so the findings come out of
this repository instead of out of general knowledge about espresso machines.
This machine has no pump, no sensors, no cup detection and no descaling
cycle, and an analysis that mentions them is about a different machine.

`doorstop` needs both flags. Without `-e`, an edit to a requirement that was
already accepted is reported as a warning and the command still exits zero.
Without `-F`, it reformats the requirement files while validating them.

One thing the flags do not buy you: a requirement whose `reviewed:` field is
still empty gets stamped automatically the first time validation runs. The
review gate applies to changing a sentence everyone already agreed to, not to
writing a new one.

## Asking for a review

Two prompts worth keeping verbatim, because both produce better answers when
asked this precisely.

**Failure modes of a requirement.** Paste the requirement and ask:

> Read this requirement and list the ways the described behaviour could fail in
> a real machine. For each one, say what the user would observe, how severe it
> is, and whether any existing test in `tests/` would catch it. Do not propose
> code. Where a failure mode is not covered by any requirement in `spec/`, say
> so explicitly.

**Review the specification against the house rules.** Ask:

> Review every requirement in `spec/` against the house rules in `AGENTS.md`.
> For each requirement give a verdict of pass, partial or fail per rule, with a
> one-line justification quoting the offending words. Report the results as a
> table. Do not edit any file.
