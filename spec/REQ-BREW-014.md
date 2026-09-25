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
reviewed: 219WVSe4YeEoeM6YIu90fyrCj01irwJpSDnwLe9Y-MQ=
risk: high
tags:
- safety
---

# Refuse to brew with an empty tank

When the user selects espresso and the water tank is empty,
the machine shall refuse to brew.

*Rationale:* dry-running the pump destroys the heating element.

## Decision

```plantuml format="svg_inline" alt="Brew decision" title="Brew decision"
@startuml
hide empty description

state "Is the water tank empty?" as TankEmpty
state "Does the tank hold less than the requested volume?" as ShortTank
state "Is the boiler below its target temperature?" as BoilerCold
state "Is the custom volume outside the allowed range?" as BadVolume
state "Refuse to brew, tank empty" as RefuseEmpty
state "Refuse to brew, not enough water" as RefuseShort
state "Refuse to start brewing" as RefuseCold
state "Reject the volume" as RejectVolume
state "Start brewing" as Brew

[*] --> TankEmpty : user requests a brew
TankEmpty --> RefuseEmpty : yes
TankEmpty --> ShortTank : no
ShortTank --> RefuseShort : yes
ShortTank --> BoilerCold : no
BoilerCold --> RefuseCold : yes
BoilerCold --> BadVolume : no
BadVolume --> RejectVolume : yes
BadVolume --> Brew : no
RefuseEmpty --> [*]
RefuseShort --> [*]
RefuseCold --> [*]
RejectVolume --> [*]
Brew --> [*]
@enduml
```