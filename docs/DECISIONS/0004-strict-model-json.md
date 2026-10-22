# ADR 0004: Strict JSON Schema model output

## Context
Generation and evaluation must cross an untrusted probabilistic boundary safely.

## Decision
Send `response_format: json_schema` with `strict=true`, repeat the schema in system
instructions, validate with extra-forbidden Pydantic models, and reject all other output.

## Alternatives considered
Free-text parsing is explicitly rejected. No tool-call alternative is documented.

## Consequences
Only compatible models/providers work. Malformed, truncated, refused, or extra-field
responses fail closed with stable errors.
