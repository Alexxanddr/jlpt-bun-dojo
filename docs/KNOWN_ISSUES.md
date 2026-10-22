# Known issues and limits

- The reviewed starter corpus covers 24 grammar points, not every pedagogical N5
  classification. JLPT publishes no authoritative complete vocabulary/grammar list.
- Valid generated or learner text can receive scope findings when local lists lack a
  word/kanji. The product labels this as dataset coverage, not a language error.
- Very short Italian/English text may be ambiguous; language detection deliberately
  accepts undetectable text.
- Deterministic grammar detection currently covers only adjacent repeated case
  particles. Target-pattern correctness requires model judgment.
- Bunpro uses an unofficial frontend API and either MCP server may change its response
  or package behavior. Integration failures remain recoverable.
- OpenRouter's free router changes backends and is rate/quota dependent. The recorded
  live check reached HTTP 429.
- Sessions, rate limits, weakness cache, and AI serialization are process-local. Multiple
  workers/replicas produce inconsistent security and study behavior.
- SQLite plus local locking has not been validated on network filesystems. Imports are
  additive and do not delete records removed upstream.
- The application is single-learner, not tenant-isolated. Demo mode blocks shared views
  but does not turn the database into a multi-user system.
- Generated sentences and expired exercises/sessions have no documented pruning policy.
- There is no password-reset flow, distributed session store, provider backoff, browser
  support matrix, or independently run penetration-test report.

No `TODO` or `FIXME` comments were present when this document was generated from commit
`7d7dcff`. Operational/security limits remain authoritative in
[SECURITY.md](../SECURITY.md); data limitations are detailed in
[DATA_SOURCES.md](../DATA_SOURCES.md).
