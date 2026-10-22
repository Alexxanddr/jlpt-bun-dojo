# Independent evaluations

Unit tests mock model output, so they prove contracts and orchestration rather than
linguistic quality. `evals/golden.json` is the initial model/rewrite comparison set.
Each entry states provenance: `derived` means an existing test or seed fixes the
expectation; `proposal` is explicitly a proposed quality check.

## Running the deterministic set

No new runner is needed. `make check` executes the same public functions and API flows
used by derived cases. A rewrite should deserialize `evals/golden.json`, run each
`deterministic` or `sm2` case, and compare required/forbidden finding codes or exact
state. Generation cases assert language, schema, local scope, same-meaning references,
and target inclusion rather than exact prose.

## Running live model comparisons

Use a disposable database and your own provider credentials. For every evaluation case:
record provider/model/settings, raw structured result, final accepted value, local
findings, latency, and error code. Pass criteria:

- schema validity is 100%; no free-text fallback or extra fields;
- deterministic expected/forbidden codes match exactly;
- a deterministic hard error is never finally accepted;
- scope-only findings are never described as proof of bad Japanese;
- explanations/suggestions use the requested source language;
- generated references are Japanese, express the prompt, stay within local membership,
  and include a selected weakness when required.

Human review is required for semantic equivalence and usefulness. Do not turn proposed
cases into deterministic product rules without reviewed evidence.

## Rewrite gate

A rewrite passes the behavioral baseline when all derived golden cases, the existing
test suite's equivalent contracts, migrations/seed counts, security boundary tests,
and both locale-key sets pass. Live model scores may vary; compare constraint pass rate
and human judgments, not byte-for-byte text.

## Browser regression checks

`npm ci`, `npx playwright install chromium`, then `make check-ui` exercise the real
frontend with controlled API responses. Coverage includes delayed/error responses,
mode transitions, settings and partial MCP sync, login/session/logout, bilingual
feedback and responsive layouts. Use `PLAYWRIGHT_CHANNEL=chrome make check-ui` to
run against installed Chrome. These tests complement API tests; they do not replace
live integration checks or human review of model output.
