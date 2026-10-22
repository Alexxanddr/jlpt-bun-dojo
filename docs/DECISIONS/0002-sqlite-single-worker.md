# ADR 0002: SQLite and one application worker

## Context
The intended deployment is one trusted learner. Sessions, rate limits, weakness cache,
and the AI lock are in memory; study state requires persistence.

## Decision
Use SQLite/WAL and exactly one Uvicorn worker or Kubernetes replica (`Recreate`).

## Alternatives considered
An external relational database/shared state store is mentioned only as future scaling
work. Rationale not documented - to confirm with the author.

## Consequences
Deployment and backup are simple, but horizontal scaling is unsupported and network
filesystem locking remains unverified.
