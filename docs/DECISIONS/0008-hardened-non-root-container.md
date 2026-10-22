# ADR 0008: Hardened non-root container

## Context
The service handles learner sentences and provider/MCP credentials in self-hosted deployments.

## Decision
Use a multi-stage image, UID/GID 10001, read-only application filesystem, writable data
volume and bounded tmpfs, dropped Linux capabilities, no privilege escalation, health
probes, no access log, and one worker. Kubernetes also disables service-account tokens.

## Alternatives considered
No deployment-hardening comparison is recorded. Rationale not documented - to confirm with the author.

## Consequences
The default runtime has a smaller privilege surface. MCP needs a larger optional Node
image, and operators remain responsible for TLS, ingress, secrets, backups, and egress.
