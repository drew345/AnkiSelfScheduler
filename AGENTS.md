# AnkiSelfScheduler Agent Guide

## Purpose and baseline

Maintain the deployed custom scheduler for AnkiDroid, with Anki Desktop compatibility where practical. Give Andrew understandable control over intervals while preserving his collections and review history.

Last verified deployment: AnkiDroid 2.24.0, scheduler v3, FSRS disabled, September 21, 2026. This is a historical tested baseline, not a claim about today's installed version. Read the current checkpoint in SESSION_LOG.md before proposing work.

## Scheduling principles

- Treat the interval previously assigned to a review card (scheduledDays) as X; never use elapsed or overdue time.
- The deployed policy is documented in README.md and implemented in src/anki-custom-scheduler.js: new/learning/relearning 25m / 40m / 3d / 6d; ordinary-review Hard/Good/Easy use 0.8X / 1.8X / 3X with a minimum base of two days, ceiling rounding, ordering safeguards and a 3,650-day cap. Again enters 25-minute relearning.
- The earlier X / 2X / 4X proposal is superseded. Do not redesign intervals merely because an archived experiment mentions another model.
- Andrew's latest stated study target is at least 17 ordinary reviews plus 10 learning/relearning cards daily, with more when time permits. Treat that as a minimum, not a fixed workload or a requested settings change.
- Keep calculations deterministic, bounded and explainable. Design new, learning and relearning behavior explicitly.

## Safety and scope

- Do not alter, import into, or reschedule real Anki collections without Andrew's explicit authorization for that exact action. Old migration authorization is historical, not standing permission.
- Treat .apkg, .colpkg, collection databases, media, card text and account data as private input. Do not commit them or derived card-level data.
- Use isolated profiles/accounts and disposable test decks for behavioral testing.
- Custom scheduling is global. Fail closed outside the exact Eng2Kor5000 and Kor2Eng5000 roots and their subdecks.
- Preserve review history and original backups. Take fresh backups before any later authorized live change; September snapshots must not overwrite newer study progress.
- Treat AnkiWeb custom-scheduling behavior as unverified until tested directly.

## Engineering workflow

1. Verify current official documentation/source when version behavior matters.
2. Express proposed interval changes as pure, testable functions with anonymized fixtures for learning, review, relearning, filtered, overdue and maximum-interval cases.
3. Simulate workload and queue effects before live use; test changes in isolation.
4. Stage any explicitly authorized deployment narrowly with deck guards and fresh backups.
5. Record meaningful outcomes in SESSION_LOG.md. Do not run archived next actions automatically.

## Queue limitation

Interval JavaScript cannot choose the next card. The September forum discussion treated the observed two-card Learn Ahead alternation as intended due-time ordering, not a demonstrated backend bug; Andrew chose not to pursue the upstream request. A shuffled round-robin experiment is optional and undeployed. If Andrew reopens it, begin with an isolated queue simulator and fairness tests before considering a maintained backend patch or separate test APK. Do not enable FSRS as an incidental fix.

## Project memory

- Default load: this file and the compact SESSION_LOG.md. Use README.md for the current policy and installation reference.
- SESSION_LOG.md owns the latest recorded checkpoint, concise outcomes, recovery pointers and optional next work.
- Historical instructions and detailed evidence are preserved in archives/memory-compaction-2026-10-08/. Search that archive only when the current task requires it; archived next steps are not an active backlog.
- Preserve meaningful history verbatim before future nontrivial compaction.
