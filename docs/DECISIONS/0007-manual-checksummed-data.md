# ADR 0007: Manual checksummed corpus imports

## Context
Language data needs provenance, stable builds, and no runtime dependency on dictionary APIs.

## Decision
Keep original seed/bundled subsets locally; require attributed manifests, confined paths,
SHA-256 verification, reviewed mappings, and transactional manual imports.

## Alternatives considered
Runtime downloads, generic PDF extraction, and automatic grammar attribution are
explicitly rejected. Further rationale is not documented - to confirm with the author.

## Consequences
Runtime is offline-capable and reproducible. Corpus updates require manual review and
additive imports do not remove stale upstream entries.
