---
name: risk-analysis
description: Produce an FMEA-style risk analysis of the coffee machine by running tools/risk_report.py and then judging what it found, with inputs, outputs, noise factors, failure modes, mitigations and corner cases derived from spec/ and the model rather than invented. Covers how to read each of the six categories, how to rank a finding by severity, how to propose the requirement that would close it, and which hardware this machine does not have and must never appear in the analysis. Use when asked for a risk analysis, an FMEA, failure modes, hazards, corner cases, what the specification does not cover, or what could go wrong with the machine.
icon: shield
color: red
---

# Risk analysis of the machine

An analysis that names a descaling cycle this machine does not have is worse
than no analysis, because it reads as authoritative and is about somebody
else's espresso machine. So the facts come out of the repository, and you only
supply the judgement on top of them.

## Always run the report first

```bash
python -m tools.risk_report
```

It reads `spec/` and `src/coffee_machine/`, prints all six tables to stdout
and writes the same analysis to `public/risk-analysis.html`. It is not a gate
and always exits zero, because it produces an argument to have rather than a
verdict.

Never write the analysis from memory or from the general shape of coffee
machines. If the command has not been run in this conversation, run it.

## What the six categories mean here

| Category | Derived from |
|---|---|
| inputs | the parameters of `brew_control.decide()`, expanded into their dataclass fields |
| outputs | the fields of `BrewResult`, plus every `Refusal` and `Warning` member |
| noise factors | integers the behaviour depends on that no requirement writes down |
| failure modes | gaps between what `spec/` agreed and what the code does |
| mitigations | the gates that exist today, and what each one catches |
| corner cases | every one of those integers and its neighbours |

Two of these are worth explaining out loud, because they are not the textbook
readings. **Noise factors** are normally physical: temperature, wear, supply
quality. This machine has no physical model at all, so the things that can
drift underneath it are the ungoverned constants; if the tank capacity
changes from 500 ml, no requirement objects and no test notices. **Corner
cases** are reported as boundaries, with a note on whether the tests name
each value literally. A value a test reaches symbolically, such as
`Drink.ESPRESSO.default_volume_ml`, reads as absent. That is not a bug in the
report; it is why this is a draft.

## Add the judgement the script cannot

For each finding, say three things the report deliberately does not:

1. **What a user would observe.** A refusal with no warning looks identical to
   a machine that is broken.
2. **How severe it is.** Anything that lets a brew start or keep going on an
   empty tank belongs at the top, because that is the damage both water
   requirements were written to prevent. Anything cosmetic goes last.
3. **Whether an existing gate would catch it.** The report answers this
   mechanically and the answer is often `none`. Say so plainly rather than
   implying the repository is safer than it is.

Rank the findings before presenting them. An unordered list of eleven items
is not an analysis.

## Never invent hardware

This machine is four dataclasses holding six integers. It has **no pump, no
sensors of any kind, no cup detection, no flow or pressure measurement, no
descaling or cleaning cycle, no notion of time, and no model of its
environment**. The words pump and heating element appear only inside the
prose of two rationales.

So none of the following may appear in an analysis of this repository:
limescale, ambient temperature, sensor drift, power dips, a stuck sensor, a
false tank reading, a debounce, or a watchdog. Every one of them presumes
something that does not exist. If the analysis would be stronger with them,
the correct response is to say which requirement is missing, not to assume
the hardware.

The same rule binds the sentences you propose. A requirement may only
describe behaviour the machine can already exhibit from the state it holds:
the tank level, the boiler temperature, the selected drink, the requested
volume. If closing a gap would need something new to be measured, say that
the hardware is a prerequisite and leave the decision with the team, rather
than writing a `shall` the machine has no way to obey.

## Closing a finding means writing a requirement

A gap is closed by an agreement, not by a patch. `CoffeeMachine.refill()`
being ungoverned is fixed by a requirement that says what refilling does, not
by deleting the method or adding a test to it. Propose the sentence, in EARS,
and hand it to the `spec-authoring` skill for the house rules and the file
anatomy. Then the ordinary gates take over: `spec_lint`, a test carrying the
new UID, and `trace_report`.
