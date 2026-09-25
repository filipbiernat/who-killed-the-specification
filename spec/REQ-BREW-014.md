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
reviewed: glL41eOxq6KFRNAcJf8SL8qiBz9lFaClb_0zzxlyhOU=
risk: high
tags:
- safety
---

# Refuse to brew with an empty tank

When the user selects espresso and the water tank is empty,
the machine shall refuse to brew.

*Rationale:* dry-running the pump destroys the heating element.