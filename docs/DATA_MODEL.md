# Data model

SQLite is opened per operation with foreign keys enabled and a ten-second timeout.
Startup enables WAL, creates `migrations`, applies unseen `trainer/migrations/*.sql`
in filename order, records each filename in the same script transaction, then seeds.
Applied migrations are immutable; changes require a new numbered file.

## Schema

| Table | Columns and constraints | Purpose |
| --- | --- | --- |
| `migrations` | `name TEXT PRIMARY KEY` | Applied migration filenames. |
| `grammar` | `id TEXT PK`; non-null `category`, `title_it`, `title_en`, `description_it`, `description_en`, `pattern` | Reviewed teaching points. |
| `sentences` | `id TEXT PK`; `grammar_id TEXT NOT NULL FK grammar`; nullable `prompt_it`, `prompt_en`; non-null JSON `refs`, `attribution` | Reviewed/imported/generated prompts and hidden references. |
| `exercises` | `id TEXT PK`; `sentence_id TEXT NOT NULL FK sentences`; non-null `language`, `prompt`, JSON `refs`, `mode`, JSON `context` default `[]`, `created_at REAL`; `hinted INTEGER NOT NULL DEFAULT 0` | One presented exercise snapshot. |
| `attempts` | `id INTEGER PK`; `exercise_id TEXT NOT NULL UNIQUE FK exercises`; non-null `answer`, JSON `result`, `quality`, `hinted`, `created_at` | Idempotent evaluated answer. Index: `attempts_created(created_at)`. |
| `reviews` | `sentence_id TEXT PK FK sentences`; non-null `repetitions`, `interval_days`, `ease`, `due` | Current SM-2 state per sentence. |
| `journal` | `grammar_id TEXT PK FK grammar`; non-null JSON `observations`, `updated_at`, `resolved DEFAULT 0` | Latest actionable observation per grammar point. |
| `settings` | `id INTEGER PK CHECK(id=1)`, `value TEXT NOT NULL` | Singleton non-secret settings JSON. |
| `provider_secrets` | `name TEXT PK CHECK(openai_api_key/openrouter_api_key)`, `value TEXT NOT NULL` | Server-only provider keys. |
| `kanji` | `literal TEXT PK`, JSON `data` | Imported KANJIDIC records. |
| `vocabulary` | `id TEXT PK`, JSON `data` | Imported JMdict records. |
| `n5_vocab` | `term TEXT PK`, `source TEXT NOT NULL` | Membership forms used by scope checks. |
| `n5_kanji` | `literal TEXT PK`, `source TEXT NOT NULL` | Membership characters used by scope checks. |
| `sources` | `name TEXT PK`, JSON `data`, `imported_at REAL` | Provenance and counts shown in progress. |

`sentences_grammar(grammar_id)` is the other explicit index. Unix seconds are stored
as `REAL`. JSON shapes are application contracts rather than SQLite constraints.

## Seed and import

`seed.json` contains arrays `grammar`, `sentences`, `vocabulary`, and `kanji`.
It currently has 24 reviewed grammar rows, 24 original bilingual sentences, 172
starter vocabulary strings, and 116 starter kanji. `INSERT OR IGNORE` makes startup
seeding additive and preserves user history. The bundled manifest then imports four
verified sources, producing 26 total sentences, 1,094 dictionary records, and 115
KANJIDIC records in the tested database. Formats, hashes, licenses, TSV rules, and
rebuild steps are authoritative in [DATA_SOURCES.md](../DATA_SOURCES.md).

## SM-2 state transition

Quality is integer 0–5. If quality `< 3`, repetitions reset to 0 and interval to one
day. Otherwise interval is 1 day for repetition 0, 6 days for repetition 1, then
`ceil(previous_interval * previous_ease)`; repetitions increment. Ease becomes
`max(1.3, ease + 0.1 - (5-quality)*(0.08 + (5-quality)*0.02))`, rounded to three
decimals. Due time is now plus interval days. Cram skips this update. A revealed hint
caps quality at 2. See [grading](GRADING.md) for score-to-quality mapping.

## History and journal

History is the newest 100 attempts joined with prompt, language, and grammar ID.
The stored `result` preserves local checks, AI result, final acceptance, grammar,
weakness context, quality, and optional next-review timestamp. Journal upserts the
latest result when an answer is rejected or has suggestions/hard errors and resets
`resolved` to false; resolving changes only that flag.
