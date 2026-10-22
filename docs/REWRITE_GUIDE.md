# From-scratch rewrite guide

## Preserve the contract

Essential behavior is the learner flow in [SPEC.md](SPEC.md), the trust and privacy
invariants in [AGENTS.md](../AGENTS.md), the SQLite/SM-2 semantics in
[DATA_MODEL.md](DATA_MODEL.md), the local-versus-AI boundary in [GRADING.md](GRADING.md),
the exact prompts/schemas in [PROMPTS.md](PROMPTS.md), and MCP filtering in
[MCP_INTEGRATION.md](MCP_INTEGRATION.md). Language/framework choice, CSS layout,
function names, and current module boundaries are incidental.

Preserve as-is, including licensing: `trainer/data/`, its manifests/hashes/licenses,
the two prompt texts and strict output schemas, stable grammar/sentence IDs, migration
meaning, locale keys/copy unless intentionally revised, and golden cases.

## Recommended order and milestone gates

1. **Corpus/database:** implement schema, ordered migration ledger, idempotent seed,
   checksum-confined imports. Gate: expected seed/import counts and repeated startup.
2. **Local language core:** NFKC, Sudachi-equivalent token record, scope findings,
   duplicate particle, kana rendering, SM-2. Gate: derived deterministic golden cases.
3. **Exercise API:** reviewed selection, modes, opaque IDs, server hints, idempotent
   answers, history/journal/stats. Gate: equivalent `tests/test_app.py` behavior.
4. **Structured providers:** independent generation/evaluation settings, exact prompts,
   strict schemas, bounded fail-closed transport, corrective generation. Gate: mock
   provider tests and every generation golden constraint.
5. **MCP:** fixed tool calls, child environment isolation, bounded extraction, N5
   admission/balancing/compaction, target verification. Gate: equivalent MCP tests.
6. **Browser:** bilingual free-writing UI, accessible controls, deterministic/AI visual
   separation, option-state matrix. Gate: locale parity and Node state tests.
7. **Security/deployment:** optional auth, origin/header/rate/body controls, CSP,
   single-worker container and manifests. Gate: security tests, `make check`, audit,
   container health and non-root inspection.

Use [EVALS.md](EVALS.md) as the cross-implementation comparison protocol.

## Solved pitfalls

- Do not infer correctness from string equality or lemma overlap.
- Do not let AI rewrite deterministic facts or turn list absence into an error.
- Do not trust provider `finish_reason`, envelope, schema, size, or redirects implicitly.
- Do not trust MCP links/HTML/fields, pass all environment secrets, or let models choose tools.
- Do not rely on client hint state, allow duplicate answer writes, or schedule cram work.
- Do not equate KANJIDIC legacy JLPT metadata/JMdict contents with a current official N5 list.
- Do not scale process-local sessions/limits/cache or shared SQLite behind multiple workers.
- Do not mutate old migrations or update corpora without attribution and hashes.

## Acceptance

The rewrite is ready only when its equivalent of `make check` is green, all derived
golden cases pass, seed/import and migration behavior match, no secret crosses the
browser/log/MCP boundary, and a local provider supports the full flow without cloud
network calls. Proposed evals inform human review but are not compatibility requirements.
