# Session Log

Current checkpoint and concise outcomes. Detailed history through September 21,
2026 is preserved verbatim in
[the original log](archives/memory-compaction-2026-10-08/SESSION_LOG.md).
October 8 was a memory-only review; it did not recheck the phone or accounts.

## Current checkpoint — last deployment verified 2026-09-21

- The one-account Korean migration is complete. The drew3452 account contains
  independent Kor2Eng5000 and Eng2Kor5000 decks. Import, collection sync and final
  phone read-back all succeeded; none is pending work.
- Historical final read-back verified 10,063 cards/notes and 489,748 linked
  reviews against the source backups, including scheduling, absolute due dates,
  content, tags and rendering. Intentional identity remapping, NFC normalization
  and at most 5 ms review-timestamp shifts were accounted for. No cards were
  graded during verification.
- Last verified baseline: AnkiDroid 2.24.0, scheduler v3, FSRS off, Learn Ahead
  80 minutes, zero new cards and Random review order. The installed script
  matched src/anki-custom-scheduler.js; [README.md](README.md) owns the deployed
  interval policy and exact deck guards.
- Andrew reported the custom timing worked well. His latest study target is
  at least 17 ordinary reviews plus 10 learning/relearning cards daily, with
  additional study when possible; this is a minimum, not a fixed workload.
- Five Burmese/Thai decks were deliberately removed from the destination only
  after authorized full-media and individual-deck backups. They remain recovery
  material, not decks awaiting migration or permission to delete their backups.
- Anki collection sync was confirmed. Separate media and Google Drive cloud
  completion were not independently confirmed; the Korean decks are text-only.

## Next action and open work

Normal study can continue; there is no queued reinstall, import or sync repair.
Wait for Andrew's requested change or new evidence from use.

The optional future workstream is shuffled round-robin Learn Ahead cycling.
Interval JavaScript does not control selection; the forum explanation treated
the two-card alternation as intended due-time ordering, not a demonstrated bug.
Andrew chose not to press the upstream request. No fork or custom APK exists.
If he reopens this work, start with an isolated queue simulator and fairness
tests. The earlier 25+5 filtered-deck, rigid 11-card quota and 1/3-second drill
ideas are historical alternatives, not authorized next actions.

## Recovery and evidence pointers

Backup base:
C:\GoogleDrive\My Drive\9b.Non Work Related\Korean Ongoing Study\Anki Backups\20260921-pre-unification

- README.md there is the source-backup manifest.
- Korean-integration-verified-v6 contains the verified directional packages,
  reports/hashes and final phone export
  drew3452_Korean-installed-verified_no-media_20260921-132301.colpkg.
- Spare-account-drew3452-Burmese-and-Thai contains preserved full-media and
  individual travel-deck backups.
- A .colpkg replaces a collection. The v6
  drew3452-integrated-TEST-ONLY.colpkg is an offline seven-deck test snapshot,
  not the final live Korean-only collection. Never restore an old snapshot over
  newer study progress without an explicitly authorized recovery plan.
- The unmodified pre-integration Korean packages share note/card identities;
  do not naively combine them. Renaming decks alone does not resolve collisions.
- Source and verification entry points: src/anki-custom-scheduler.js and
  tools/verify_phone_export.py. Detailed package paths, hashes, transform
  invariants and recovery evidence remain in the archived log and backup
  manifests. Do not open private collections merely to load project context.

## Concise history

### 2026-10-08 — Memory compaction

On ROBERTSLGGRAM17, preserved the prior AGENTS.md, README.md and SESSION_LOG.md
byte-for-byte in archives/memory-compaction-2026-10-08/ and recorded SHA-256
preservation evidence. Replaced obsolete startup policy with the deployed
rules, separated the completed migration from optional queue work, and corrected
README's pending-migration wording. Application code, collections and accounts
were unchanged.

### 2026-09-21 — Integration completed and installed

Recovered a verified transformation checkpoint into the v6 deliverables;
import/reimport and all-card rendering checks passed. Seven scheduler tests and
21 backend state samples passed during the recorded work. The original
transformer's later fixes compiled but were not used for a full successful
rebuild; v6 was completed from the recovered checkpoint. Live installation and
independent phone read-back then passed. Earlier v1-v4 partial workspaces and
their resume instructions are history, not deliverables.

### 2026-09-20 — Queue question separated from timing

Investigated Learn Ahead contraction, received the intentional-ordering
explanation and stopped upstream escalation. Optional round-robin work remains
separate from the working interval scheduler.

### 2026-09-03 to 2026-09-07 — Timing deployed and positively reviewed

Implemented guarded interval rules, verified rollback backups, installed in
the original separate accounts and received positive live-study feedback.
Those old account names and proposed policies are superseded by the current
checkpoint above.
