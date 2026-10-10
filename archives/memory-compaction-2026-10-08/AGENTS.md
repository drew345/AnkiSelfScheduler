# AnkiSelfScheduler Agent Guide

## Purpose

Build and evaluate a custom scheduler for AnkiDroid, with compatible behavior on Anki Desktop where practical. The scheduler should give the learner direct, understandable control over intervals instead of silently reproducing Anki's native scheduling decisions.

## Current target

- AnkiDroid 2.24.0
- Scheduler v3
- FSRS disabled
- Custom scheduling JavaScript
- Anki Desktop compatibility for testing and maintenance

## Scheduling principles

- Treat the interval previously assigned to a review card (`scheduledDays`) as `X`.
- Never substitute elapsed or overdue time for `X`; overdue cards must not receive an accidental interval explosion.
- The working review-button model is a short same-day retry followed by approximately `X`, `2X`, and `4X`. Exact coefficients and bounds remain subject to simulation and review.
- New, learning, and relearning behavior must be designed explicitly rather than inherited without examination.
- Account for a daily review cap of about 30 and the deliberate choice not to clear every due card each day.
- Keep calculations deterministic, bounded, and explainable. Respect a maximum interval unless a later design decision changes it.

## Safety and scope

- Do not alter, import into, or reschedule the user's real Anki collections unless the user explicitly authorizes that exact action.
- Treat `.apkg`, collection databases, media, card text, and account data as private input. Do not commit them or derived card-level data.
- Use isolated Anki profiles/accounts and disposable test decks for behavioral testing.
- Custom scheduling is configured globally. Any deployed script must fail closed and act only on explicitly named deck roots or prefixes.
- Preserve review history and backups. Prefer read-only analysis and reversible experiments.
- Treat AnkiWeb custom-scheduling behavior as unverified until tested directly.

## Engineering workflow

1. Confirm behavior against current official Anki/AnkiDroid documentation or source when version details matter.
2. Express the scheduling policy as pure, testable functions before producing deployable JavaScript.
3. Build anonymized fixtures covering new, learning, review, lapse/relearning, filtered-deck, overdue, and maximum-interval cases.
4. Simulate workload, bunching, short-term cycling, and interval growth before live use.
5. Test in an isolated profile, then stage deployment narrowly with explicit deck guards.
6. Record meaningful findings and decisions in `SESSION_LOG.md`; keep it concise and current.

## Known product constraint

Custom scheduling can change proposed states and intervals, but it may not control AnkiDroid's card-selection order. The observed loop in which a few short-step cards repeat while other waiting cards are skipped therefore needs separate investigation and may require workflow, queue, or upstream-app changes.

## Project memory

- Read this file and `SESSION_LOG.md` before substantial work.
- Update `SESSION_LOG.md` after decisions, experiments, or implementation milestones.
- Keep durable rules here; keep dated progress, evidence, open questions, and next actions in the session log.
