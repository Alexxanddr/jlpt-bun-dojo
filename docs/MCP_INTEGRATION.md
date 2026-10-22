# MCP integration

MCP is optional and disabled in saved settings by default. The administrator supplies
stdio executable/JSON arguments and one source-specific token through environment.
Only PATH, SYSTEMROOT where present, and that server's token reach the child; stderr is
discarded. Startup commands are trusted administrator configuration, never model input.

## Synchronization

`POST /api/mcp/sync` requires MCP enabled, runs both clients concurrently under the
global AI lock, and stores combined items plus unavailable source names only in process
memory. Restart clears the cache. Each session has a 25-second total timeout, 20-second
read timeout, 128 KiB combined response limit, and a fixed tool allowlist.

### Bunpro

Call exactly `get_weak_items({"limit": 15})`. Read at most 15 objects from each
`grammar` and `vocab` group. Keep only bounded scalar factual fields; synthesize
`subject_type` as grammar or vocabulary. The public server is documented in README.

### WaniKani

Call exactly `list_review_statistics({"percentages_less_than": 80})`. Recursively
inspect at most depth 8/30 findings and 500 children per list. For the first ten valid
subject IDs, call `get_resource({"resource":"subjects","id": subject_id})`; accept
only known subject types and bounded slug, characters, and five meanings.

HTML, external links, unknown fields, and over-size detail responses are discarded.

## N5 admission and balancing

1. Bunpro grammar is eligible only when its normalized level is `N5` or `5`.
2. Bunpro vocabulary title must exactly occur in local `n5_vocab`.
3. WaniKani kanji characters must exactly occur in local `n5_kanji`.
4. WaniKani vocabulary/kana-vocabulary characters or slug must occur in local
   `n5_vocab`; radicals are never eligible.
5. Preserve input ranking, take at most three items for each `(source, subject_type)`,
   then at most ten total.
6. Compact each accepted item to source, target, kind, meanings, and accuracy before UI
   or model use.
7. Every generated Japanese reference must contain at least one selected lexical target, matched against text
   or Sudachi surface/lemma/normalized forms, and every reference must pass local scope
   checks. Grammar labels guide the model but are not searched literally: constructions
   need contextual judgment. Corrective retry receives only validation facts.

## Trust and failures

MCP content is serialized in the model's user-data object and is explicitly described
as untrusted, never instructions. It cannot select commands or tools. Missing commands
produce empty lists; malformed args, transport/tool/JSON/time/size failures mark that
source unavailable without discarding the other source. Targeted practice reports
separately: sync required, no locally compatible N5 items, or provider generation failure.

The administrator must still trust installed MCP executables and should sandbox
process/network access when required. See [SECURITY.md](../SECURITY.md).
