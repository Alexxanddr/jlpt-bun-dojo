# Reliability and interface review

## Design direction

The interface follows the `design-taste-frontend` app-screen workflow: **Editorial
Greeting**, seed **1758861913**, with the existing system typefaces and ink/teal
palette retained. No remote fonts or runtime frontend dependencies were added.
The face is a cool writing-paper surface; the product-specific element is the Japanese
composition sheet, with the source meaning above the answer and feedback below it.

The previous interface placed a large heading and every option above the exercise.
The new desktop layout uses a 12-column grid: three columns for practice options,
nine for writing, with 16px gutters. Tablet and phone layouts collapse the options
and put the five destinations in a bottom navigation bar.

## Objects and jobs

- An exercise has a source language, grammar point, prompt, mode and reference answers.
- Only one exercise is active; its answer is limited to 500 characters.
- A learner writes their own sentence, asks for an example, then requests evaluation.
- Four evaluation scores range from 0 to 100; they are model feedback, not certainty.
- Local checks remain separate from model explanations and suggestions.
- Reviews have due dates; intensive practice does not change the spaced-review schedule.
- The grammar journal groups observations by grammar point and supports resolution.
- Progress reports real attempt counts and six axes, including honest zeros.
- Settings select providers and models; secret inputs clear after saving.
- MCP synchronization supplies bounded Bunpro and WaniKani evidence, including partial results.
- The main job is repeated daily writing on desktop or phone, with minimal setup overhead.

## Screen questions

| Screen | First question | Next action |
| --- | --- | --- |
| Practice | What meaning am I expressing in Japanese? | Write and evaluate |
| History | What did I write and what feedback did I receive? | Open feedback |
| Grammar journal | Which constructions need attention? | Review and resolve |
| Progress | What have I practised, and what is due? | Return to practice |
| Settings | Which providers and study sources are active? | Save or save and synchronize |

## Verification and critique

The rendered empty screen was inspected at 1440, 768 and 390px. Writing, feedback,
settings and progress were also captured from browser regression fixtures. The second
visual pass reduced the heading, removed the decorative textarea gradient, collapsed
phone controls and shortened the mobile journal label after the Italian text clipped.
The prompt now dominates the writing sheet, and the answer is visible on the first
phone screen. Numeric scores use tabular figures; progress shares the same teal hue.

The source linter reports zero failures/warnings. The rendered inspector reports zero
unwaived failures and one warning. Two observations are intentional:

- `no-title` is waived because the inspector selects the first `h1` in the DOM, which
  belongs to the hidden login view. Each active view has its own visible heading;
  screenshots and browser assertions verify the practice title.
- `hero-void` flags the unused area below the empty writing sheet on a large screen.
  This is a first-run state, with no exercise or feedback to invent. The actual writing
  and feedback screens occupy that area naturally.

No values are invented in the application. README screenshots use the explicitly
synthetic browser fixture in `tests/browser.test.cjs`: “I am a student.”, “学生です。”,
one accepted attempt, no due reviews, and sample model scores. They demonstrate the
interface rather than measuring model quality or exposing a learner's history.

## Reliability coverage

Backend checks cover authentication and passwordless/demo modes, origin and input
boundaries, settings/key retention, generation and provider failures, MCP normalization
and partial availability, local language checks, hints, review/cram scheduling,
history, journal resolution, progress and data imports.

Browser checks use the real HTML, styles and JavaScript with controlled API responses.
They cover delayed evaluation, failed generation, HTML proxy failures, mode switching,
secret clearing, save-before-sync, partial MCP results, language changes, expired
sessions, wrong passwords, logout and desktop/tablet/phone layout. They deliberately
do not claim to prove live model quality or every third-party outage condition.
