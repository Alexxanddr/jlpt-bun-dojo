# Changelog

All notable changes to JLPT Bun Dojo are documented here.

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
