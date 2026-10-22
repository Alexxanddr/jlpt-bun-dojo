# ADR 0001: Sudachi for local Japanese analysis

## Context
The product needs reproducible lemma, POS, reading, and inflection data without a runtime dictionary service.

## Decision
Use SudachiPy with `sudachidict-core`, NFKC normalization, and SplitMode A.

## Alternatives considered
No comparison is recorded. Rationale not documented - to confirm with the author.

## Consequences
Analysis works locally and tests use the real tokenizer. The installed dictionary/version
affects results and increases the environment size.
