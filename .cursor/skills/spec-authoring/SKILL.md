---
name: spec-authoring
description: Write, reword and review requirements in spec/ using EARS syntax and this project's house rules. Covers the five EARS patterns, the one-shall rule, the anatomy of a requirement file, and the Doorstop commands that validate and accept a change. Use when asked to write a new requirement, add a requirement to the specification, reword an existing one, split a requirement that does two things, add a subchapter or a diagram to a requirement, judge whether a sentence is a real requirement or a wish, or explain why doorstop reports a requirement as unreviewed.
icon: book-open
color: orange
---

# Authoring requirements

A requirement is one sentence that a test can fail against. Everything else in
the file is metadata or explanation.

## The five EARS patterns

Pick the one that matches the situation. Do not invent a sixth.

| Pattern | Shape | Use it when |
|---|---|---|
| ubiquitous | `The <actor> shall <behaviour>.` | The behaviour always holds. |
| event-driven | `When <trigger>, the <actor> shall <behaviour>.` | Something happens and the machine responds. |
| state-driven | `While <state>, the <actor> shall <behaviour>.` | The behaviour holds for as long as a condition lasts. |
| optional feature | `Where <feature>, the <actor> shall <behaviour>.` | The behaviour only applies to a variant or option. |
| unwanted behaviour | `If <condition>, then the <actor> shall <behaviour>.` | Something has gone wrong and the machine must react. |

Write requirements as ordinary sentences. The keyword that opens one takes a
capital because it begins a sentence; `shall`, and any keyword landing in the
middle, stay lowercase. The linter is case-insensitive, so the all-capitals
spelling used in EARS textbooks and on slides passes too, but the files
themselves read as prose rather than as shouting.

Choosing between `when` and `if` is the judgement call that comes up most
often, and the answer follows the trigger rather than the mood of the
sentence. A trigger can carry an unwelcome qualifier without becoming unwanted
behaviour, which is where most of the confusion comes from.

Compare the two requirements in this repository that both concern an empty
tank. `REQ-BREW-014` reads *When the user selects espresso and the water tank
is empty* — the trigger is the selection, something the machine expects, and
the empty tank only narrows the circumstances in which it applies.
`REQ-BREW-021` reads *When the machine refuses to brew because the water tank
is empty* — the trigger is the refusal, which is the machine doing precisely
what `REQ-BREW-014` told it to do. An empty tank is unwelcome; neither
sentence is about anything going wrong.

So: if you can name the thing the user, the hardware or the machine itself
just did, it is `when`, however unwelcome the surrounding state. `if` is for a
condition that should never have arisen at all. This machine has no way to
detect one, which is why nothing in `spec/` uses that pattern today, and why
proposing one means proposing the hardware that would notice it.

## The house rules

1. **One `shall` per requirement.** Two `shall` clauses mean two requirements.
   Split them and give each its own UID. A test written against a double
   requirement can only half-fail, which makes the result meaningless.
2. **No `shall`, no requirement.** `should`, `may`, `will` and "the machine
   handles" are wishes. Rewrite or delete.
3. **Name a covering test** in `references:`. A normative requirement with an
   empty `references:` field fails `tools/spec_lint.py`.
4. **Describe behaviour, not implementation.** A tank capacity is
   configuration; refusing to brew is behaviour. If a sentence names a class,
   a function or a file, it has drifted into design.
5. **Make the sentence decidable.** If two engineers could disagree about
   whether the machine complied, the sentence is not finished. Prefer "reject
   any volume below 25 ml" over "keep the volume sensible".

## Anatomy of a requirement file

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

The heading is a short human label, not the requirement. The requirement is
the sentence under it. `*Rationale:*` explains why the requirement exists and
is ignored by the parser.

`reviewed:` is a hash of the requirement as last accepted. Editing the prose
invalidates it, which is how Doorstop notices that a requirement drifted away
from what was agreed.

## Subchapters and diagrams

The first heading and the sentence under it are the requirement. Everything
after a second heading (`##`) is commentary: `tools/spec_loader.py` stops
reading there, so a subchapter, a diagram or notes can live in the same file
without becoming a second requirement. Put it after the rationale, and keep
`shall` out of it: the linter ignores the commentary, a reviewer does not.

A diagram is a PlantUML fenced block. This one is a complete state diagram
that renders; keep its shape and replace the labels, the heading included:

````markdown
## <What the diagram shows>

```plantuml format="svg_inline" alt="<The same, for the image>" title="<The same>"
@startuml
hide empty description

state "First question?" as First
state "Second question?" as Second
state "Outcome when yes" as Yes
state "Outcome when no" as No

[*] --> First : trigger
First --> Yes : yes
First --> Second : no
Second --> Yes : yes
Second --> No : no
Yes --> [*]
No --> [*]
@enduml
```
````

Declare every state as `state "Label" as Alias` before the transitions, and
use only the aliases in the transitions. A quoted label inside a transition
makes PlantUML take the block for a sequence diagram, and what gets published
is a picture of a syntax error. Line breaks inside a label are `\n`.

It is rendered by the public PlantUML server when the document is published,
so `doorstop publish` needs network access. A diagram that fails still comes
back as an image, so publishing succeeds either way; check the page instead. Commentary is part of the body, so
adding it invalidates `reviewed:` like any other edit.

## Adding a requirement

```bash
doorstop add REQ-BREW           # allocates the next UID and writes a stub
```

Then write the sentence, set `risk` and `tags`, and point `references:` at the
test file that will cover it.

Two fields in the stub need attention, because Doorstop's defaults are not
what this document wants:

- **`level:`** decides where the requirement lands in the published document,
  and Doorstop's guess is rarely the right place. The document has three
  sections, each one a `normative: false` file whose level ends in `.0`:
  `REQ-BREW-100` for the drink catalogue at `1.x`, `REQ-BREW-200` for the
  refusals at `2.x`, and `REQ-BREW-300` for what reaches the display at `3.x`.
  Choose the section by meaning and take the next free number inside it. A
  requirement that fits none of them needs a new section file before it needs
  a level, and that is a conversation to have rather than a number to invent.
- **`keyword:`** inside `references:` is load-bearing and validated. Doorstop
  checks that the string appears **literally** in the referenced file, so it
  has to be the UID and the covering test has to spell that UID out — which
  the `@pytest.mark.requirement("REQ-BREW-014")` marker does. Get it wrong and
  you get `external reference not found`, which does not explain itself.

Verify before finishing, from the project virtualenv (see `AGENTS.md`):

```bash
python -m tools.spec_lint         # EARS and the house rules
pytest tests/test_spec_quality.py
doorstop review REQ-BREW-014      # after editing an existing requirement
doorstop -e -F                    # tree validation
doorstop publish all ./public --template spec
! grep -q "Syntax Error" public/documents/REQ-BREW.html   # fails if a diagram broke
```

After an edit, `doorstop -e -F` reports the requirement as unreviewed until
its new wording is accepted. That is the gate doing its job, not a fault, and
Doorstop's source will not tell you more than this paragraph does: review the
UID you changed, then validate again. Review that UID only; `doorstop review
all` would also accept edits nobody asked you to make.

Be aware of what the review step does and does not mean. A **new** requirement is
stamped automatically the first time validation runs, so `doorstop review`
changes nothing for it. The review gate exists for **edits**: once a sentence
carries a stamp, changing it makes `doorstop -e -F` fail until somebody
accepts the new wording. Treat the command as the act of agreeing, and treat
the stamp on a new requirement as the weaker thing it is.

Finish with the address of the requirement in the published document, alone
in a `text` code block so it can be copied and pasted into a browser. Every
requirement is an anchor named after its UID:

```text
file:///C:/path/to/repo/public/documents/REQ-BREW.html#REQ-BREW-014
```

Do not make it a Markdown link: the editor opens a clicked `file://` link as
source, and the browser drops the anchor when the file is opened for it. Build
the path from the repository root with forward slashes; in Git Bash, `pwd -W`
prints it with the drive letter.

## Reviewing someone else's requirement

Read it aloud and ask three questions in order. Which EARS pattern is this?
What single observable behaviour would a test assert? Could a reasonable
engineer read this sentence and build something different from what I pictured?

The third question is the one that finds real defects. Report the offending
words verbatim rather than paraphrasing them.
