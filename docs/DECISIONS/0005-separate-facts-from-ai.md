# ADR 0005: Separate deterministic facts from AI judgment

## Context
Model feedback is useful but cannot certify grammar or redefine locally reproducible facts.

## Decision
Compute local findings first, pass them as data to evaluation, display them separately,
and let deterministic hard errors override model acceptance. List absence is scope only.

## Alternatives considered
A model-only grader and exact-reference matching are contradicted by tests/instructions.
Further rationale is not documented - to confirm with the author.

## Consequences
Users can distinguish facts from suggestions. Local grammar coverage stays intentionally
narrow and semantic correctness still depends on probabilistic judgment.
