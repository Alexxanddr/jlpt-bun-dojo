# Functional specification

## Purpose and learner

JLPT Bun Dojo helps one self-hosting beginner actively produce Japanese around JLPT
N5 material. The learner receives meaning in Italian or English, writes Japanese
without choices, and sees verifiable local observations separately from model advice.
It is practice software, not an official certification or a complete N5 syllabus.

## User flows

1. **Free practice:** choose prompt language and optional grammar category. Use a
   reviewed local sentence, or request an AI sentence at easy, standard, or challenging
   difficulty. Easy is short/single-clause; standard is natural; challenging combines
   two N5 ideas while remaining in local scope.
2. **Answer:** enter 1–500 Japanese characters. Optionally reveal one to three reference
   translations. Submit once; repeating the same exercise returns the stored result.
3. **Feedback:** see acceptance, four 0–100 AI dimensions, deterministic findings,
   explanation, suggestions, corrections, valid variants, and next review time.
4. **Due review:** receive the earliest sentence whose review is due. A scored attempt
   updates its schedule.
5. **Cram:** receive the earliest scheduled sentence regardless of due time. The attempt
   is recorded but leaves the schedule unchanged.
6. **History:** inspect the latest 100 attempts.
7. **Grammar journal:** inspect unresolved or resolved observations grouped by grammar
   point and mark an entry revisited.
8. **Progress:** view attempts, due count, per-grammar success, source metadata, cached
   MCP evidence, and radar axes for grammar, vocabulary, register, coverage,
   independence, and scheduled-review recall.
9. **Targeted practice:** enable MCP, synchronize, then generate from locally admitted
   Bunpro/WaniKani weaknesses. Empty, unavailable, or out-of-scope results produce an
   explicit recoverable error.
10. **Settings:** select interface/prompt language, category, independent generation and
    evaluation providers/models/temperatures/token limits, compatible endpoint, keys,
    and MCP enablement. Blank key inputs retain existing server-side secrets.

## Behavior and edge cases

- Reviewed prompts can be filtered by category; missing filters/reviews return no exercise.
- A missing IT/EN translation is generated from the stored Japanese reference.
- AI generation is valid only for free or targeted modes. Targeted mode always generates.
- Wrong prompt language, out-of-scope references, or absent weakness targets are retried;
  final failure saves no generated exercise.
- A deterministic error can reject an answer the model accepted. Scope observations cannot.
- Revealing a hint caps scheduling quality at 2, even if the client omits that fact later.
- Failed provider evaluation saves no attempt. A completed answer is idempotent.
- Password authentication is optional. Public demo mode exposes practice while blocking
  settings mutation, MCP sync, history, journal, and aggregate statistics.

## Non-functional requirements

- Local-first and offline-capable with a local model after installation; no runtime
  dictionary service, telemetry, CDN, or remote font.
- One trusted learner and one worker/replica; not multi-tenant.
- SQLite persistence, additive migrations, idempotent seed/import, and preserved history.
- Bounded input/provider/MCP data, fail-closed structured AI output, same-origin browser
  access, secret redaction, and hardened container deployment. See [security](../SECURITY.md).
- Italian and English UI/prompt parity; keyboard-visible focus and Japanese text input.
- Attributed, locally stored corpus data. See [data sources](../DATA_SOURCES.md).

## Non-goals

- Official JLPT certification, exhaustive N5 coverage, or proof that an absent term is wrong.
- Multi-user accounts, tenant isolation, distributed sessions, or horizontal scaling.
- Autonomous dictionary downloads, model tool use, or AI-authored deterministic errors.
- Grammar parsing comprehensive enough to certify arbitrary Japanese.

## To confirm

- No product roadmap or required browser support matrix is documented.
- The intended policy for pruning generated exercises and expired sessions is undocumented.
