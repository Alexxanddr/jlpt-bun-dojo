# Changelog

All notable changes to JLPT Bun Dojo are documented here.

## Unreleased

- Redesign the study workspace with separate practice options, a focused writing sheet,
  responsive navigation, clearer feedback and bilingual success/error states.
- Serialize browser operations to prevent mixed exercises, hints and evaluation results;
  preserve drafts on failed requests and make completed answers read-only.
- Save settings before MCP sync, clear key inputs after saving, and show usable partial results.
- Preserve sentence identity and review scheduling when translating a review prompt.
- Count hints requested while evaluation is running; apply lexical weakness checks to
  every reference without treating grammar labels as literal vocabulary.
- Report model output limits separately and add corrective instructions for schema retries.
- Add browser regression tests to CI alongside the API, provider and data checks.

- Publish a dedicated MCP container image and use it in Kubernetes so the Bunpro and
  WaniKani server executables are available at runtime.

## 0.1.4 - 2026-10-22

- Added application screenshots and one-click Render deployment documentation.
- Added a restricted public demo mode that protects shared data and provider settings.
- Made the container honor Render's dynamic `PORT` while retaining local port 8000.

## 0.1.3 - 2026-10-22

- Made instance authentication optional when `APP_PASSWORD` is empty or absent.
- Hid login and logout controls in passwordless mode while retaining origin, request
  header, rate-limit and input validation protections.

## 0.1.2 - 2026-10-22

- Fixed inconsistent AI generation and difficulty controls when switching practice modes.
- Locked exercise options while a sentence is being prepared to prevent request/UI state races.
- Added the exercise-mode state matrix to CI.

## 0.1.1 - 2026-10-22

- Added a third corrective generation attempt for targeted or challenging exercises
  while retaining strict local N5 validation.

## 0.1.0 - 2026-10-22

- Added bilingual JLPT N5 writing practice with deterministic checks and structured AI feedback.
- Added configurable local/OpenRouter generation and evaluation models.
- Added difficulty controls, SM-2 reviews, cram mode, history, journal, and statistics.
- Added Bunpro `get_weak_items` and WaniKani weakness targeting with local N5 filtering.
- Added Docker, optional published MCP packages, Kubernetes manifests, and CI workflows.
- Added attributed offline language datasets, security controls, and validation documentation.
