# Reference data and reproducible imports

The bundled `trainer/data/seed.json` is original MIT content: 24 beginner
patterns, one IT/EN pair each and a small teaching vocabulary/kanji list. It is not
an exhaustive or official N5 inventory. Dataset absence is always a scope note.
Bundled attributed subsets (separate licenses, see `trainer/data/manifest.json`):
1,094 JMdict common entries selected by starter/Tanos spellings; 115 KANJIDIC2
entries selected by the starter kanji list; Tanos-derived N5 spellings/readings
via elzup/jlpt-word-list; two Tatoeba Japanese sentences with four direct IT/EN
translations. Original sentences and teaching lists remain separate from these
third-party data. Kanji and grammar coverage is curated, not an exhaustive Tanos
kanji/grammar import. The dictionary subset does not itself define an N5 level.

## Manual update

1. Obtain snapshots from the sources below. Keep originals, licenses and dates.
2. For dictionaries, use the JSON or `.json.gz` files from a **dated** release of
   [jmdict-simplified](https://github.com/scriptin/jmdict-simplified/releases).
   JMdict uses `words[]`; KANJIDIC2 uses `characters[]`. Entries are retained with
   POS, readings, meanings, radicals and legacy JLPT metadata in local tables.
3. Prepare reviewed Tanos and Tatoeba TSVs as described below. Review their level,
   grammar mapping and license before importing. Generic PDF extraction and
   automatic grammar attribution are deliberately not treated as reliable data.
4. Put everything under `imports/`, excluded from Git. Compute SHA-256 for each file:
   `shasum -a 256 imports/kanjidic2-en.json.gz`.
5. Write `imports/manifest.json`, replacing sample values with real hashes/paths:

```json
{"sources":[
  {"name":"kanjidic2-YYYYMMDD","kind":"kanjidic","file":"kanjidic2-en.json.gz",
   "sha256":"REPLACE_WITH_64_HEX_DIGITS","license":"CC-BY-SA-4.0",
   "url":"https://github.com/scriptin/jmdict-simplified/releases",
   "attribution":"James William Breen and the EDRDG; converted by jmdict-simplified"},
  {"name":"jmdict-YYYYMMDD","kind":"jmdict","file":"jmdict-eng.json.gz",
   "sha256":"REPLACE_WITH_64_HEX_DIGITS","license":"CC-BY-SA-4.0",
   "url":"https://www.edrdg.org/edrdg/licence.html",
   "attribution":"James William Breen and the EDRDG; converted by jmdict-simplified"},
  {"name":"tanos-n5-YYYYMMDD","kind":"tanos","file":"tanos.tsv",
   "sha256":"REPLACE_WITH_64_HEX_DIGITS","license":"RECORD_VERIFIED_TERMS",
   "url":"https://www.tanos.co.uk/jlpt/jlpt5/","attribution":"Jonathan Waller / Tanos"},
  {"name":"tatoeba-YYYYMMDD","kind":"tatoeba","file":"tatoeba.tsv",
   "sha256":"REPLACE_WITH_64_HEX_DIGITS","license":"CC-BY-2.0-FR",
   "url":"https://tatoeba.org/en/downloads","attribution":"Tatoeba contributors, see per-row authors"}
]}
```

Run `make update-data MANIFEST=imports/manifest.json`. Export `DATABASE_PATH` if
using a non-default path. `make seed` reapplies original exercises and imports missing bundled snapshots.
`make update-data` without MANIFEST reimports the bundled manifest.
All source files are verified before import. Imported changes are one transaction;
a failed source rolls back all changes in that update. Repeated imports upsert
records and don't duplicate rows. Existing study history is preserved. Snapshots
are additive: deletions in newer source releases are not automatically propagated.
The source manifest, counts and import dates are stored in `sources` and shown in UI.
Keep the manifest and original licenses with database backups.

## Tanos TSV

Download the N5 kanji/vocabulary/grammar lists from
[Tanos](https://www.tanos.co.uk/jlpt/jlpt5/). Review the site's current reuse terms
and preserve attribution. The origin domain was unavailable during implementation. The bundled vocabulary
uses the attributed [elzup mirror](https://github.com/elzup/jlpt-word-list), which
traces the data through chyyran/jlpt-anki-decks and jamsinclair/open-anki-jlpt-decks
to Jonathan Waller. Tanos' indexed [sharing statement](https://www.tanos.co.uk/jlpt/sharing/)
licenses non-sold material as Creative Commons BY without specifying a version.
Preserve that statement and the mirror's MIT notice; don't relabel data as solely MIT.

UTF-8 tab-separated header: `type`, `term`, `grammar_id`. Types:

- `kanji`: exactly one CJK character in `term`; empty grammar_id.
- `vocab`: Japanese spelling/reading in `term`; empty grammar_id. Each token's
  surface, dictionary form and normalized form is indexed for matching.
- `grammar`: original pattern text in `term`, matching reviewed seed ID in
  `grammar_id` (e.g. `object`, `past`, `request`). Add a reviewed grammar row and
  exercise to the original seed when no mapping exists; don't mislabel higher levels.

Tanos drives local membership lists. JMdict does not contain reliable universal
N5 labels. KANJIDIC's old JLPT metadata is preserved without equating old level 4 to N5.
The starter teaching list is retained alongside imports; inspect provenance before
using membership results as educational evidence.

## Tatoeba TSV

Use the [Tatoeba exports](https://tatoeba.org/en/downloads), including author and
license information, and select short Japanese sentences with direct IT/EN links.
Review grammar and meaning; a lemma overlap is insufficient to assign a pattern.

Required TSV header (tabs, not commas):

```
ja_id	ja	ja_author	source_id	language	text	source_author	grammar_id
```

`language` is `it` or `en`. The same `ja_id` and `grammar_id` merges both languages.
Authors must be present. Sentences over 60 Japanese or 300 source characters are
excluded; all Japanese vocabulary/kanji must pass current local membership checks.
Import Tanos before Tatoeba. Each row retains sentence IDs, authors, license and
canonical URL. Show/copy attribution when redistributing the resulting corpus.
Missing IT/EN prompts are translated by the generation provider on request,
conditioned on the existing Japanese reference. They are marked AI-generated and
remain unreviewed; they don't become attributed human translations.

## Runtime boundary

No import job runs at startup or per request. Runtime network traffic is restricted
by application code to the configured AI endpoint/OpenRouter and explicitly enabled
MCP processes. Use network policy/firewall rules if enforced egress is required.
There are no live Jisho/kanjiapi requests and no browser fonts/CDNs.

## Bundled snapshot provenance and rebuilding

`trainer/data/snapshot-inputs.json` records original archive hashes, dated release,
mirror commit and Tatoeba query. Bundled output hashes are in `manifest.json`.
Dictionary subsets preserve upstream structures and tags, including POS/readings/
radicals/legacy JLPT. The subset selection is a modification under the same CC BY-SA
4.0 terms. License text is in `trainer/data/licenses/`.

To rebuild using the preserved original snapshots:

```sh
uv run python scripts/build-bundled-data.py jmdict.zip kanjidic.zip n5.csv tatoeba-books.json
make update-data
```

The Tatoeba selection is explicitly reviewed by IDs (219639 and 233021), with exact
direct translation IDs. Its two original Japanese sentences and both translations
are preserved in `tatoeba.tsv`; no sentences with ambiguous matches are imported.
The input API is used only during this manual maintenance, never at app runtime.
Live APIs may change; retain original input snapshots to reproduce their hashes.
