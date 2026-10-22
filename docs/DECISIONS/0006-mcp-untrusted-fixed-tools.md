# ADR 0006: Treat MCP as untrusted data behind fixed tools

## Context
Bunpro/WaniKani weaknesses improve targeting, while third-party processes and payloads
can expose secrets, change shape, or contain instructions.

## Decision
Administrators choose executables; application code chooses fixed tools and arguments,
passes a minimal child environment, bounds responses, strips fields, locally filters N5
scope, and serializes compact facts as untrusted model data.

## Alternatives considered
Model-selected MCP tools and raw payload forwarding are explicitly disallowed.

## Consequences
Prompt-injection and leakage surface is smaller; adapter changes may be needed when
unofficial APIs evolve, and executable trust still belongs to the administrator.
