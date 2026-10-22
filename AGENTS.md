# Agent guide

**Tool compatibility:** this file is the single source of truth for Codex, Claude Code, Cursor, Copilot, Gemini CLI, Aider, and other coding agents.

JLPT Bun Dojo is a self-hosted JLPT N5 free-writing trainer. A FastAPI service stores
study state in SQLite, performs local Sudachi checks, and obtains schema-constrained
generation/evaluation from either an OpenAI-compatible endpoint or OpenRouter.
Bunpro and WaniKani MCP integrations are optional; the browser is dependency-free.

## Verified commands

```bash
uv sync --frozen                         # install locked Python and development dependencies
make dev                                 # http://127.0.0.1:8000, reading .env
make check                               # Ruff, mypy, pytest
npm ci && npx playwright install chromium
make check-ui
uv run pip-audit
docker build -t jlpt-bun-dojo:local .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env jlpt-bun-dojo:local
docker compose up --build -d --wait
docker compose -f docker-compose.yml -f docker-compose.mcp.yml up --build -d --wait
docker compose down
```

`uv` may need a writable cache, for example `UV_CACHE_DIR=/tmp/jlpt-uv-cache` in a
restricted sandbox. Live AI/MCP checks require administrator credentials and quota.

## Repository map

- `trainer/app.py`: lifecycle, middleware, HTTP routes, orchestration, statistics.
- `trainer/ai.py`: provider adapter, exact model instructions, strict response handling.
- `trainer/models.py`: API and model-output Pydantic contracts.
- `trainer/grading.py`: deterministic findings, kana rendering, SM-2 update.
- `trainer/tokenizer.py`, `trainer/language.py`: NFKC/Sudachi and IT/EN detection.
- `trainer/db.py`, `trainer/migrations/`: SQLite connection, migrations, seed startup.
- `trainer/import_data.py`: offline, checksummed, transactional corpus imports.
- `trainer/mcp_client.py`: fixed stdio MCP tools, bounded extraction and N5 filtering.
- `trainer/data/`: original seed and attributed immutable bundled snapshots.
- `trainer/static/`: plain HTML/CSS/ES modules and matched `it`/`en` locale files.
- `tests/`: pytest behavior/security tests and Node UI-state tests.
- `scripts/`: manual seeding and bundled-data maintenance.
- `k8s/`, `Dockerfile`, `docker-compose*.yml`, `render.yaml`: one-worker deployments.
- `.github/workflows/`: CI, container publication, opt-in Strix scan.
- `docs/`: product, architecture, data, grading, provider, MCP, eval and rewrite docs.

## Observed conventions

- Python 3.12; four-space indentation; snake_case functions and variables; small modules.
- Ruff selects `E4`, `E7`, `E9`, `F`, `I`, targets py312, and uses line length 110.
- mypy checks untyped function bodies and ignores missing third-party stubs.
- Pydantic request/output models inherit `StrictModel` and forbid extra fields.
- User-facing failures use stable short codes translated in both locale JSON files.
- Provider/MCP exception bodies and learner content are not logged; logs contain codes/types.
- SQL values are parameterized. Server code selects the few dynamic table/column names.
- Tests use temporary SQLite databases, real Sudachi, mock HTTP/MCP transports, and direct asserts.
- UI text belongs in both locale files; preserve key parity, keyboard focus, and Japanese input.

## Non-negotiable invariants

Ask the maintainer before changing any item below.

1. Deterministic findings remain server-owned and separate from probabilistic AI advice.
2. Model responses use strict JSON Schema and Pydantic validation; no free-text parsing fallback.
3. MCP/browser/model content is untrusted data, never executable instructions.
4. Secrets are not returned to the browser, included in errors, logged, or forwarded to unrelated children.
5. Missing local vocabulary/kanji is a scope limitation, not proof of incorrect Japanese.
6. Generated Japanese references pass local N5 checks before storage.
7. No telemetry, analytics, remote fonts, runtime dictionary APIs, or automatic corpus downloads.
8. The app can use a fully local OpenAI-compatible provider; cloud AI is optional.
9. Data imports are manual, attributed, checksum-verified, path-confined, and transactional.
10. Existing attempts/reviews survive seed and import reruns; failed evaluation stores no partial attempt.
11. Hints are tracked server-side; cram attempts do not alter the SM-2 schedule.
12. One application worker/replica is required because sessions, rate limits, MCP cache, and AI lock are in memory and SQLite is shared locally.
13. Same-origin mutation header, body/rate limits, CSP, and non-root deployment hardening remain intact.
14. The project makes no official or complete JLPT N5 coverage claim.

## Do not touch casually

- Do not edit `uv.lock` by hand; regenerate it with `uv` after dependency changes.
- Do not edit bundled `.json.gz` files or imported TSV data without updating manifests,
  SHA-256 values, attribution, licenses, and reproducibility records.
- Do not rewrite or reorder migrations that may already be recorded in user databases;
  add a new numbered migration.
- Do not commit `.env`, databases, source archives, credentials, or live learner text.
- Do not edit generated/runtime state under `var/`.

## Workflow and definition of done

Read the relevant documents below and grep all callers before changing shared behavior.
Work in small verifiable steps. Add one meaningful regression test for non-trivial logic.
Run `make check`; also run the Node test for UI-state changes and `uv run pip-audit`
for dependency changes. Update both locales for UI copy and `CHANGELOG.md` for user-visible
changes. A change is done when relevant checks pass, docs/config/callers agree, secrets
stay out of the diff, and `git diff --check` is clean.

Start with [the functional specification](docs/SPEC.md), then use
[architecture](docs/ARCHITECTURE.md), [data model](docs/DATA_MODEL.md),
[grading](docs/GRADING.md), [model prompts](docs/PROMPTS.md), [providers](docs/MODELS.md),
[MCP](docs/MCP_INTEGRATION.md), [evaluations](docs/EVALS.md), and the
[rewrite guide](docs/REWRITE_GUIDE.md). Existing operational truth remains in
[README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), and [DATA_SOURCES.md](DATA_SOURCES.md).
