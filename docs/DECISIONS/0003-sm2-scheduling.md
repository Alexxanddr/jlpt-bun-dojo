# ADR 0003: SM-2 scheduling

## Context
Due review needs a small deterministic per-sentence schedule derived from answer quality.

## Decision
Store repetitions, interval days, ease, and due time; update them with the SM-2 formula.
Hints cap quality at 2 and cram mode does not update scheduling.

## Alternatives considered
No alternatives are recorded. Rationale not documented - to confirm with the author.

## Consequences
Scheduling is transparent and testable. A single latest state exists per sentence and
the algorithm does not model user-specific parameters beyond that state.
