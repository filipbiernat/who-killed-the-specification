---
active: true
derived: false
level: 3.1
links: []
normative: true
ref: ''
references:
- keyword: REQ-BREW-021
  path: tests/test_brew_control.py
  type: file
reviewed: vGJgQAa-d2Kotp6sUeZr7qqgKMlRAu7DMNNON9XNUeI=
risk: high
tags:
- display
- safety
---

# Tell the user why the machine refused

When the machine refuses to brew because the water tank is empty,
the machine shall promptly show a refill warning on its display.

*Rationale:* a machine that silently does nothing reads as broken, and the
user starts pressing buttons instead of refilling the tank.