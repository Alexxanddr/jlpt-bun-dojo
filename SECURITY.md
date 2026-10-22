# Security

## Intended deployment

Single trusted learner, one worker/replica, private self-hosted instance. The browser
and AI/MCP output are untrusted; the administrator controlling environment variables,
provider endpoints, dataset manifests and MCP executables is trusted. This is not a
multi-tenant service. Protect the host, backups, container volume and cluster Secrets.
Report vulnerabilities privately to the repository owner's GitHub security advisory
channel after publication; do not attach keys, personal sentences or DB files.

## Controls implemented

- Optional instance password (at least 16 characters when set); constant-time
  comparison, random 256-bit session tokens, HttpOnly/SameSite=Strict cookies,
  12-hour expiry, logout revocation. Sessions live in memory and reset on restart.
  An empty or missing `APP_PASSWORD` disables authentication and is intended only
  for localhost or a trusted private network.
- Same-origin UI/API; exact configured Origin checks and required custom header on
  mutations; no permissive CORS. `APP_ORIGIN` must match scheme/host/port. The health
  endpoint and static UI are public but contain no user or provider secrets.
- Global mutation budget of 20/minute, including login; AI calls are serialized.
  One worker is required. A shared-instance user can exhaust this budget, so this
  limit is not a substitute for tenant isolation. Add proxy limits for public ingress.
- Request bodies limited to 8 KiB while streaming, answer length 500, schema-bound
  language/mode/settings, SQL parameters and server-selected column/table names.
  Passwords and keys do not appear in validation errors.
- CSP restricts scripts/styles/connect to self, frame embedding disabled, no sniffing,
  no referrer, camera/microphone/geolocation disabled. HSTS is sent when
  `COOKIE_SECURE=true`; terminate TLS at a trusted proxy and set the exact origin.
- UI uses `textContent` and DOM creation, never model-generated HTML/innerHTML.
- API keys come from process environment/cluster Secrets or web settings.
  Saved keys are stored server-side and never returned to the browser. Provider URLs
  reject embedded credentials, query strings and non-HTTP schemes; requests do not
  follow redirects. Local-network endpoints are intentional for local inference.
- Model inputs are serialized as user data separate from system instructions. AI
  has no tools, filesystem, database execution or access to other providers' secrets.
  Only strict JSON schema responses passing Pydantic validation are consumed;
  truncated or refused responses fail closed. This limits impact of prompt injection;
  it cannot guarantee honest scoring or detect every semantic instruction attack.
- Deterministic findings are separate server-owned fields. Models cannot create
  hard errors or override duplicate-particle failures. Membership absence is a scope
  observation, not a language error. Failed evaluations don't save partial attempts.
- Provider response stream limited to 256 KiB, 60-second timeout; response bodies
  and exceptions are never returned/logged. API access logs disabled in run recipes.
  A provider can retain submitted sentences; choose local inference for offline use.
- Optional MCP calls use a fixed tool allowlist through the official SDK, bounded
  extracted responses and a 25-second total timeout. Child processes receive only
  PATH/platform variables and their own token; stderr is discarded. The administrator
  must trust installed executables. The MCP image installs versioned public packages
  during its build. MCP data is untrusted model context and UI text.
- Dataset update is manual, local-only, checksummed, attributed and transactional;
  manifests cannot escape their directory. No runtime dictionary downloads.
- Docker is non-root with a read-only app filesystem and no Linux capabilities;
  Kubernetes disables service-account token mounting and specifies resource limits.
- No telemetry, analytics, remote fonts or tracking. Pinning uses `uv.lock`; CI
  runs pip-audit against installed locked packages.
- `DEMO_MODE=true` blocks provider settings, MCP synchronization, history, journal,
  and statistics. The demo database is still shared and ephemeral; opaque exercise
  IDs limit access to individual active attempts but do not provide tenant isolation.

## Verification record

Source review and regression tests cover authentication/origin checks, response
headers, rate and body limits, secret-free settings, strict AI schemas, provider
error redaction, retry/idempotency, SM-2/cram, real morphology, mock MCP environment
isolation and checksummed imports. See `tests/` and CI for reproducible checks.
This is an implementation review, not an independent penetration-test certificate.

A manual opt-in Strix workflow is supplied, based on the installed Strix CI skill.
It requires administrator-supplied LLM credentials and provider quota. Strix was
not installed/run during implementation. The named “cloudflare security audit” skill
was unavailable; the requested header/input/injection/rate/CORS/key controls above
were reviewed directly. No Cloudflare service is required or used.

## Remaining validation and limitations

- Run end-to-end with your selected LM Studio/OpenRouter model and token-authorized
  MCP servers; automated tests use mocks and don't validate real model quality.
- Review the full imported corpora, their licenses and N5 mappings before redistribution.
- Public exposure requires `APP_PASSWORD`, HTTPS and a correctly configured ingress/firewall. The
  app does not implement password reset, per-user accounts or distributed sessions.
- MCP response schemas, child-process behavior, DNS and outbound egress are not
  confined by application validation alone. Use an OS/container/network sandbox
  if stronger containment is needed. The default image contains no Node runtime; the optional MCP target includes Node.
- SQLite full dictionary import may require additional disk and time; back up the
  volume before updates. Additive snapshots don't automatically delete stale entries.
- Authentication secrets live in the process environment; protect process access.
  Python's runtime cannot promise zeroization of secret strings.

### Local validation on 2026-10-22

See [TEST_RESULTS.md](TEST_RESULTS.md) for the actual test matrix and live-provider
results. Ruff, mypy, 51 pytest checks, JavaScript syntax, dependency audit, both
Docker builds, container HTTP flow, restart persistence and both live MCP
connections were checked. Local Gemma structured generation/evaluation worked.
OpenRouter authenticated but its exhausted free daily quota prevented completing
post-fix live evaluation. No Kubernetes resources were applied and no independent
Strix penetration test was run. Targeted practice passed after filtering Bunpro and
WaniKani inputs against the local N5 lists;
finite-corpus membership remains an explicit limitation.
