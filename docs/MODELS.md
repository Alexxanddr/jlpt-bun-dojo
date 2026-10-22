# Model providers

`AIClient` exposes two purposes, `generation` and `evaluation`, each with its own
provider, model, temperature, and token limit. Both use OpenAI Chat Completions and
require strict `response_format: json_schema` support.

## Providers

- `openai`: any administrator-configured HTTP(S) OpenAI-compatible `/v1` base URL.
  Embedded credentials, query strings, fragments, and non-HTTP schemes are rejected.
  A key is optional because local servers commonly require none.
- `openrouter`: fixed `https://openrouter.ai/api/v1`, requires an OpenRouter key, and
  sends `provider.require_parameters=true` so the routed backend must accept requested
  parameters. `openrouter/free` may choose different free backends.

Requests have a 60-second timeout, do not follow redirects, and accept at most 256 KiB.
Only `finish_reason=stop` and a Pydantic-valid schema response succeed. HTTP 429 maps to
`provider_rate_limited`; other HTTP/transport failures and malformed envelopes are
redacted to stable codes. Malformed/schema-invalid output gets one corrective retry.
Output-limit truncation returns `provider_incomplete` immediately so the learner can
raise the token budget. HTTP errors and timeouts are not retried. There is no provider
or free-text fallback.

## Settings precedence

On first use, provider/model/base URL defaults come from `.env`; Pydantic supplies
language, category, temperatures (0.2), token limits (2000), and MCP defaults.
Once web settings exist, their JSON supplies non-secret configuration. Provider keys
come first from `provider_secrets`, otherwise from environment. A blank web key does
not overwrite the saved key. Keys are excluded from serialization and only boolean
configured status reaches the browser.

Generation creates a prompt plus one to three Japanese references and may run two
attempts, or three for targeted/challenging work. Evaluation grades an existing learner
answer with at most two structured attempts. See [PROMPTS.md](PROMPTS.md) and [GRADING.md](GRADING.md).

## Operational characteristics

The global async lock serializes model calls, so latency is additive. Local inference
keeps learner text on the configured host and has no API cost; actual model quality and
speed depend on that server. OpenRouter sends learner content to a third party, may
retain it under its policy, incurs provider latency, and its free router is quota- and
backend-dependent. The repository records successful local Gemma structured calls and
HTTP 429 from the free OpenRouter quota in [TEST_RESULTS.md](../TEST_RESULTS.md); it
does not contain a general cost benchmark.

## To confirm

- No minimum model size, context length, or supported-model matrix is documented.
- No retry/backoff policy exists for provider HTTP errors; corrective retries apply
  to schema-invalid output and to structurally valid generation output that fails local validation.
