---
active: true
derived: false
level: 2.3
links: []
normative: true
ref: ''
references:
- keyword: REQ-BREW-015
  path: tests/test_brew_control.py
  type: file
reviewed: G95Wd4t4bYBQTUWgh7--Y-QMPQUVqRFK0jnh5v2gKC0=
risk: high
tags:
- safety
---

# Refuse to brew without enough water for the cup

When the user requests a brew and the water tank holds less water than the
requested volume, the machine shall refuse to brew.

*Rationale:* a tank that is not empty is not the same as a tank that is
enough. A brew started on the last few millilitres finishes on a dry pump,
which is the failure REQ-BREW-014 exists to prevent.