---
active: true
derived: false
level: 2.1
links: []
normative: true
ref: ''
references:
- keyword: REQ-BREW-002
  path: tests/test_brew_control.py
  type: file
reviewed: VDxHpUcXaqHSG-F5wos_mEx29ukhTMZHiMB1nzwyBpA=
risk: medium
tags:
- boiler
---

# Do not brew with a cold boiler

While the boiler is below its target temperature,
the machine shall refuse to start brewing.

*Rationale:* water pushed through the grounds too cold makes undrinkable
coffee, and the user blames the beans rather than the machine.