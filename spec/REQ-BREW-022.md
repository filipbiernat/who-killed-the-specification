---
active: true
derived: false
level: 3.2
links: []
normative: true
ref: ''
references:
- keyword: REQ-BREW-022
  path: tests/test_brew_control.py
  type: file
reviewed: Y1ZQD0p8sS32fL6xjBuOqh1Uf12Qkw2awhcM2bYo4j8=
risk: medium
tags:
- display
---

# Never refuse silently

When the machine refuses to brew for a reason other than an empty water tank,
the machine shall show a warning naming that reason on its display.

*Rationale:* REQ-BREW-021 covers the empty tank. Every other refusal was
silent, which looks identical to a machine that is simply broken.