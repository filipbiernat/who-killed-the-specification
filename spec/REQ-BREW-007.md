---
active: true
derived: false
level: 1.2
links: []
normative: true
ref: ''
references:
- keyword: REQ-BREW-007
  path: tests/test_brew_control.py
  type: file
reviewed: vAHDnVK7MzxyP1_yALfpBN7wlMx2Hv9y4xekTcOOETs=
risk: low
tags:
- catalogue
---

# Keep custom volumes within the safe range

Where the selected drink has a custom volume,
the machine shall reject any volume below 25 ml or above 250 ml.

*Rationale:* below 25 ml the pump cannot build pressure, and above 250 ml
a single dose of grounds is already exhausted.