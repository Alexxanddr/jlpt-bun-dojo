# Contributing

Use Python 3.12, `uv sync --frozen`, then `make check`. Keep changes focused and add
one meaningful regression test for non-trivial behavior. Run `uv run pip-audit`
when changing dependencies; commit updated `uv.lock`.

UI copy belongs in both `trainer/static/locales/it.json` and `en.json`. Keep keyboard
navigation, visible focus, source/feedback language, and Japanese composition input
working. Don't add third-party browser requests or provider keys to UI code.

New grammar patterns require a stable ID, IT/EN titles/descriptions, bilingual
exercise and reviewed Japanese references in `trainer/data/seed.json`. Never claim
an LLM suggestion is deterministic. External corpora require provenance, licensing,
checksums and reviewed level mappings. Don't add copied data without attribution.

Use numbered SQL migrations and preserve exercise/review history. Test repeated
migration/seed execution. Don't expose a shared SQLite deployment with multiple
workers. Live AI/MCP checks are opt-in and must use your own credentials.

See SECURITY.md for private reporting. No credentials, `.env`, user databases or
third-party import archives belong in a pull request.
