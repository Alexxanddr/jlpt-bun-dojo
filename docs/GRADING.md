# Grading pipeline

## Deterministic analysis

`trainer.grading.deterministic` receives the learner answer, hidden Japanese
references, local vocabulary/kanji sets, and target pattern.

1. `normalize` applies Unicode NFKC and trims outer whitespace.
2. SudachiPy tokenizes in SplitMode A. Every token records surface, dictionary form,
   normalized form, reading, full POS tuple, and out-of-vocabulary status.
3. Lemma similarity excludes particles, auxiliary verbs, punctuation, and whitespace,
   then reports the maximum Jaccard similarity between answer and any reference,
   rounded to three decimals. It is evidence, never acceptance logic.
4. Each CJK character absent from `n5_kanji` creates deterministic
   `kanji_not_listed`, severity `scope`.
5. Each noun, verb, adjective, or adverb whose surface, lemma, and normalized form are
   all absent from `n5_vocab` creates deterministic `vocabulary_not_listed`, severity
   `scope`.
6. Adjacent identical case particles in `{を, が, に, で, へ}` create
   `duplicate_particle`, severity `error`. This is the only implemented local hard error.
7. Inflectional token form/type pairs are returned for inspection. The target pattern
   is echoed, but `pattern_check` is explicitly `requires_contextual_judgment`.

No other grammar rule is deterministic. In particular, local membership absence is a
finite-dataset scope observation and does not make valid Japanese incorrect.

Generated references pass the same checks. Known N5 vocabulary written with an
unlisted kanji is rendered in kana when Sudachi provides a usable reading; unknown
vocabulary is never hidden this way.

## AI evaluation

After local checks, the evaluation model receives source language, source prompt,
answer, grammar metadata, and the complete local-check object. It returns strict JSON:

- grammar, vocabulary, register, and intent integer scores from 0 to 100;
- probabilistic `accepted`;
- source-language explanation and up to eight suggestions;
- up to three corrections and three valid variants.

The model is instructed to accept omitted pronouns, natural word order, kana, synonyms,
and valid alternatives; treat similarity as evidence only; and label concerns beyond
the supplied findings as uncertain suggestions. Exact prompts and schemas are in
[PROMPTS.md](PROMPTS.md).

Final acceptance is `AI accepted AND no deterministic severity=error finding`.
Scope findings do not override the model. The response UI labels local findings as
verifiable checks and model output as probabilistic judgment.

## Scheduling quality

The minimum of the four scores drives quality. A rejected answer maps to
`min(2, floor(min_score/20))`; an accepted answer maps to
`max(3, min(5, floor(min_score/20)))`. A server-recorded or client-reported hint caps
quality at 2. Non-cram attempts feed this quality into the SM-2 transition documented
in [DATA_MODEL.md](DATA_MODEL.md).

## Failure behavior

Provider/schema/refusal/truncation failure returns a stable error and stores no attempt.
Repeating an already evaluated exercise returns its prior stored result. Model content
cannot create deterministic findings or erase the duplicate-particle override.
