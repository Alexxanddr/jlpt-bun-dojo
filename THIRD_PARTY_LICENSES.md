# Third-party notices

Application source and original starter exercises: MIT, see LICENSE. That license
does not relicense external dictionaries, imported sentences or morphology data.

| Component/data | License / attribution |
| --- | --- |
| FastAPI | MIT, Sebastián Ramírez and contributors |
| Uvicorn | BSD-3-Clause, Encode and contributors |
| HTTPX | BSD-3-Clause, Encode and contributors |
| Pydantic | MIT, Pydantic contributors |
| MCP Python SDK | MIT, Anthropic and contributors |
| Lingua language detector | Apache-2.0, Peter M. Stahl and contributors; local IT/EN language models |
| ijson | BSD-3-Clause, Ivan Sagalaev and contributors |
| SudachiPy | Apache-2.0, Works Applications and contributors |
| SudachiDict core | Apache-2.0 with upstream dictionary notices, Works Applications; includes derived lexicographic resources, see the installed distribution notices |
| JMdict / KANJIDIC2 (bundled subset; optional full imports) | James William Breen and the Electronic Dictionary Research and Development Group; CC BY-SA 4.0 subject to the [EDRDG license statement](https://www.edrdg.org/edrdg/licence.html) and source-specific conditions |
| jmdict-simplified snapshots (bundled subset; optional full imports) | Converted by scriptin/jmdict-simplified; derivative dictionary license remains applicable, see [upstream notices](https://github.com/scriptin/jmdict-simplified#license) |
| Tatoeba sentences (bundled subset; optional full imports) | CC BY 2.0 FR, or verified per-sentence CC0; Tatoeba contributors, preserve sentence IDs, authors and [license details](https://tatoeba.org/en/downloads) |
| Tanos-derived N5 vocabulary (bundled) | Jonathan Waller / Tanos, Creative Commons BY (version unspecified in upstream sharing statement); via chyyran/jlpt-anki-decks, Jamie Sinclair and elzup; mirror MIT notice retained in `trainer/data/licenses/tanos-mirror-MIT.txt` |

Transitive code dependencies and development tools retain their distribution
licenses. `uv.lock` records exact package versions. Keep package license files in
container distributions; don't strip `.dist-info` notices. Check the source archive
and installed dictionary license/readme for detailed Sudachi lexicon attributions.

Imported data tables and exported corpora must keep their own attribution and
share-alike conditions; the application's MIT license applies to code only.
KanjiVG and audio datasets are not included.

Bundled Tatoeba attribution: #219639 by **mookeee**, English #56960 by **CK**,
Italian #373938 by **Pharamp**; #233021 by **bunbuku**, English #515538 by **CK**,
Italian #499809 by **Pharamp**. All selected records declare CC BY 2.0 FR, see
[license deed](https://creativecommons.org/licenses/by/2.0/fr/). Text is unmodified;
selection, bilingual merging and N5 grammar annotations are this project's changes.
Canonical sentence URLs: https://tatoeba.org/en/sentences/show/219639 and
https://tatoeba.org/en/sentences/show/233021. Attribution is retained per language
in SQLite and displayed with the exercise.

Bundled dictionaries derive from jmdict-simplified release
`3.6.2+20261019180022`. Copyright James William Breen and EDRDG; see
`trainer/data/licenses/CC-BY-SA-4.0.txt`, upstream license links and snapshot hashes.
Modifications consist of selecting records, compressing JSON and indexing locally.
