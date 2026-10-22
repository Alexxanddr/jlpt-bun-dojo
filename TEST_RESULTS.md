# Validation — 2026-10-22

Tests used the administrator's `.env` without printing credentials. Live study
attempts were stored in separate disposable smoke-test databases/volumes, not the
application's normal history. The `.env` was not modified.

| Check | Result |
| --- | --- |
| Ruff | Passed |
| mypy | Passed, 10 application modules |
| pytest | 55 passed; one upstream Starlette HTTPX deprecation warning |
| JavaScript syntax | Passed |
| Exercise mode UI state | Passed for free, targeted, review and cram transitions |
| Optional authentication | Passwordless Docker instance opened directly; login/logout hidden; password mode retained |
| Public demo mode | Practice allowed; settings, MCP and shared-data endpoints blocked |
| pip-audit | No known vulnerabilities reported |
| Docker base build | Passed |
| Docker MCP build | Passed |
| Compose base/MCP configuration | Passed |
| Kustomize render | Passed; no manifests applied to the configured cluster |
| Docker healthcheck | Healthy |
| Container hardening | UID/GID 10001; read-only root filesystem; capabilities dropped |
| Authentication, cookies, CSP, protected history | Passed via real container HTTP API |
| API responses/logs | Configured keys/tokens/password not found in checked settings response or container logs |
| Seed exercise, IT/EN locales | Passed |
| Local model discovery | Configured Gemma model present on the configured endpoint |
| Local structured generation | Passed on host and in Docker, including local N5 membership filtering |
| Local structured evaluation | Passed on host/container path |
| Correct reference / wrong intent | Correct reference accepted; unrelated answer rejected by local Gemma |
| Hint tracking | Hint penalty retained server-side |
| Answer retry | Same result returned without duplicate attempt |
| History/statistics | Attempt persisted and counted |
| Container restart | Attempts retained; old session invalidated |
| Bunpro MCP | `get_weak_items` connected; 15 grammar and 15 vocabulary records returned |
| WaniKani MCP | Connected successfully; 30 bounded weakness records, with subject details |
| MCP from Docker | Both published packages available without host bind mounts |
| OpenRouter authentication | Key accepted |
| OpenRouter evaluation | Blocked by HTTP 429: free daily quota exhausted |
| Targeted MCP selection | 10 balanced N5 records from Bunpro and WaniKani across grammar, kanji and vocabulary |
| Targeted challenging generation | Three consecutive live runs passed with both MCP servers available |

## Fixes made after live checks

- OpenRouter previously returned JSON with unexpected field names. The request now
  requires provider parameter support and includes the exact schema in the system
  instructions as well as `response_format`. Pydantic still rejects every response
  outside the contract; no text-parsing fallback was added. A successful real
  OpenRouter evaluation **after** this change remains unverified because of quota.
- HTTP 429 now produces a distinct localized provider-rate-limit error. Invalid
  envelopes and invalid structured output produce `invalid_provider_response`;
  provider bodies are never returned in errors.
- Generation instructions/schema descriptions explicitly require one source prompt
  and Japanese-only alternatives with the same meaning. Local vocabulary and kanji
  constraints are passed to generation. This corrected a real output containing
  English translations mixed into Japanese references. Validation is retained for
  cases where a model still ignores those constraints.
- A targeted generation initially used an out-of-scope WaniKani word and was
  correctly rejected. WaniKani subjects are now filtered against local N5
  vocabulary/kanji before generation, excluding radicals. If no eligible subject
  remains, a localized message is returned without calling the model. The live
  targeted test then passed with 6 eligible records.
- Added a Docker MCP target that installs the versioned public Bunpro and WaniKani
  packages at build time. It does not depend on sibling repositories or stale bind
  mounts. Bunpro grammar/vocabulary and WaniKani results are balanced after N5 filtering.
- Targeted and challenging generation now gets a third corrective attempt. The
  strict local N5 guard remains unchanged; a regression test verifies the retry count.

## Remaining limits

Free OpenRouter evaluation needs retesting after quota resets. The free router may
select different models, so one successful call would not certify every backend.
Generative outputs can still be rejected by the finite local N5 list, including in
targeted practice; the app fails closed rather than admitting unchecked references.
Only a few real-language samples were evaluated, not a linguistic benchmark.
No Kubernetes deployment, image-CVE scanner or independent Strix penetration test
was performed. GitHub Actions and the GHCR publishing workflow passed for v0.1.0.

The application is started using the MCP Compose overlay at http://localhost:8000.
It uses the configured providers and password. MCP remains an explicit UI setting;
enable it and sync in Settings when wanted. Smoke-test attempts are separate.

The repository rename was verified with the `jlpt-bun-dojo-data` Docker volume. Eight
existing attempts and all three migrations remained available after copying from the
previous volume; the original volume was retained.

## Regression: generated prompt language

A reported Italian exercise displayed “I like cats.” because the generation
response was schema-validated but its actual language was not checked. Generation
now explicitly names the source language in system instructions and validates the
prompt with a local IT/EN Lingua detector. One retry preserves the Japanese
references; a second wrong-language response fails without saving the exercise.
Regression tests cover the exact reported sentence, both languages, preservation
of existing references and absence of database writes on persistent failure.
Live local-model checks returned “Mi piace il pesce.” for Italian and “I like cats.”
for English. Short shared/ambiguous expressions are intentionally not rejected.

## Regression: generated N5 references rejected

The reported message was the generated-reference scope guard, not a container
crash. Historical logs contained only startup because handled rejections were
silent. Safe categorical warnings now record scope codes, AI HTTP statuses and
validation exception types without prompts, references, response bodies or keys.

Known N5 words using out-of-list kanji are rendered with Sudachi readings before
scope validation, preserving inflection and katakana loanwords. Unlisted vocabulary
is never hidden by conversion. Failed scope checks are returned to the generator
for one further attempt; the final guard still prevents saving unchecked output.
Tests cover advanced kanji in a known word, conjugation, loanwords, unknown words,
retry feedback and log-content privacy.
