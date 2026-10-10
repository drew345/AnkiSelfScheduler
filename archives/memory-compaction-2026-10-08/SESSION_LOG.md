# Session Log

## 2026-09-03 — Repository initialization

### Goal

Assess and eventually implement a custom Anki scheduling system centered on AnkiDroid 2.24.0. The immediate task is to establish this repository and preserve enough project memory for safe continuation.

### User's working model

- After a miss or while learning: short same-day retry choices, then roughly 1, 2, and 4 days.
- For established review cards: a short retry followed by choices based on the prior assigned interval `X`, tentatively around `X`, `2X`, and `4X` (possible alternatives include `0.8X`, `1.6X`, and `3X`).
- The first short option should keep a forgotten card cycling today until recalled.
- The user normally allows zero new cards and limits daily reviews to about 30 while maintaining roughly 3,000–3,500 introduced vocabulary cards.

### Read-only backup analysis

Inputs were two exported packages kept outside this repository:

- English-to-Korean: `zEK5000-20260903145933.apkg`
- Korean-to-English: `Kor to Eng 5000-20260903150120.apkg`

No package, database, media, or card content is to be committed here.

Both collections passed database integrity checks. Both use scheduler v3 with FSRS off, 30 reviews/day, 0 new cards/day, a 2,000-day maximum interval, hard factor 1.0, starting ease 2.0, easy bonus 2.0, and a 25-minute lapse step. English-to-Korean new steps are 20/25 minutes with 1/2-day graduation; Korean-to-English new steps are 20/40 minutes with 1/6-day graduation.

The backlog is not simple bunching:

- English-to-Korean: 2,979 of 3,687 active review cards due; median overdue 287 days; 1–2-day cards are 47.3% of due cards and 1–7-day cards are 61.9%.
- Korean-to-English: 2,904 of 3,779 active review cards due; median overdue 303 days; 1–2-day cards are 39.5% of due cards and 1–7-day cards are 52.1%.
- Ease is pinned near 1300 on 83.6% and 88.5% of introduced/review-like cards respectively.
- Recent answers are overwhelmingly Again or Hard. Same-day histories confirm repeated cycling of a small subset of cards.
- Native scheduling can turn a very overdue 1–2-day card into a many-month Good interval and a multi-year Easy interval. This supports basing custom choices on the prior assigned interval rather than elapsed overdue time.

The two decks share 4,873 note GUIDs. That explains why importing both descendants of the same original list into one collection can merge or conflict. A safe migration strategy is a separate future concern from scheduling.

### Technical findings

- The custom scheduler receives proposed card states plus context and can change the displayed and applied intervals.
- Relevant inputs include `scheduledDays`, `elapsedDays`, ease, lapses, relearning state, and deck name.
- It does not expose a dependable card ID, tag, note field, or preset identifier for scoping.
- Deployment must therefore use an exact deck-name/root-prefix guard and leave every unmatched state unchanged.
- AnkiDroid supports custom scheduling in this version, but exact cross-client and AnkiWeb behavior still needs controlled testing.
- The 80-minute Learn Ahead limit makes 25/38-minute steps immediately eligible, but changing it does not necessarily solve unfair queue selection. Custom scheduling may not be able to enforce round-robin selection among waiting cards.

### Decisions

- Do not let overdue time inflate `X`; use the previous assigned interval.
- Do not modify the live collection while the policy is unsettled.
- Design learning/relearning and mature-review rules as one coherent policy.
- Build a simulator and automated fixtures before producing a live script.
- Fail closed outside explicitly targeted decks.

### Open questions

- Exact short retry timings and whether they should adapt to the number of cards still in circulation.
- Final multipliers, rounding, minimum intervals, and maximum-growth safeguards.
- Desired treatment after a lapse and criteria for graduating out of short intervals.
- Whether acceptable AnkiDroid settings can reduce short-card starvation, or whether an upstream change/add-on is needed.
- How to test synchronization and AnkiWeb behavior without risking either live account.

### Next action

Specify the scheduler as a small state machine, run it against anonymized distributions resembling both backups, and compare workload and interval outcomes before writing deployable custom-scheduling JavaScript.

### Repository state

Initialized locally and pushed to `https://github.com/drew345/AnkiSelfScheduler` on branch `main`. The initial repository contains only project memory and privacy-oriented ignore rules; no Anki exports or card data were added.

## 2026-09-03 — Due-count clarification and study cadence

- The user often studies opportunistically, sometimes only once per week rather than daily. Any workload simulation must model irregular sessions, not assume daily completion.
- “Currently due” is not a FIFO count ahead of a newly scheduled card. It includes overdue cards of every stored interval, including the one-day cards themselves.
- At export, English-to-Korean had 732 due cards with a stored one-day interval and 678 with a two-day interval. Korean-to-English had 650 and 498 respectively.
- The due one-day cards were already a median 298 days overdue in English-to-Korean and 276 days overdue in Korean-to-English.
- In the prior 365 days, 498 English-to-Korean and 472 Korean-to-English reviews ended with a one-day interval; none of those cards had a subsequent recorded review by export time. The user's perceived quick returns likely refer mainly to intraday 25/37.5-minute relearning repetitions before the one-day graduation.
- A one-, two-, or four-day interval makes a card eligible on that date; it does not guarantee that the card will be selected then when thousands of other due cards compete under a daily cap.
- Proposed architecture should separate a protected recently-touched/relearning lane from backlog sampling. Interval JavaScript alone may be insufficient because it does not control queue selection.

## 2026-09-03 — Queue allocation and rollout preference

- The user prefers each session to draw approximately 25 recently encountered cards and 5 old backlog cards.
- A two-filter filtered deck is the leading no-fork queue mechanism: one search gathers due recently rated cards with a limit of 25, and a second gathers due older cards with a limit of 5. The exact definition of “recent” and ordering still need to be chosen.
- Custom scheduling JavaScript will remain responsible for the button intervals; the filtered deck supplies the card-selection layer that JavaScript lacks.
- The user prefers real-world rollout on the current vocabulary collection instead of a synthetic test list. Use current backups plus a fresh pre-deployment export, make the first change reversible, and inspect outcomes after a small number of genuine sessions.
- Do not bulk redistribute the backlog merely to make the due count look cleaner. If the two-lane session works, the backlog can remain intact and be recalibrated progressively as five cards per session enter active circulation.

## 2026-09-03 — Timing-first direction

- The user clarified that a normal session starts with 11 deliberately retained must-see-next-session learning/relearning cards plus 30 newly selected due reviews, for 41 cards, and ends with 11 deliberately retained again.
- Delay filtered backlog injection for now. The user may raise newly selected reviews from 30 to 35 and study more frequently.
- Timing changes alone cannot select untouched backlog cards, but they can prevent reviewed cards from recycling too quickly and thereby free future session capacity.
- A 3/6/15-day choice set is appropriate as a recovery tier for short-interval cards, not as a permanent maximum. With thousands of active cards, well-known cards must have a gradual path to intervals measured in months or years.
- Avoid native jumps directly from a 1–2-day stored interval to roughly one year. Proposed direction: apply minimum choices around 3/6/15 days to short cards, then use bounded multipliers as the stored interval grows.

## 2026-09-03 — Simplified working timing model

- Remove the proposed separate short-review tier. There will be only a special post-miss/relearning rule and one ordinary-review multiplier rule.
- Immediately after a miss, retain two intraday choices followed by longer exits: approximately `<25m / <40m / 3d / 6d`.
- Once a card is back in ordinary review, calculate Hard/Good/Easy from its previously assigned interval `X`: approximately `0.8X / 1.8X / 3X`; Again returns it to the post-miss rule.
- Use ceiling-to-whole-day rounding, preserve strict button ordering, cap at the configured maximum interval, and use an effective minimum base of two days so the large legacy population of one-day cards receives useful choices instead of `1d / 2d / 3d`.
- Example Easy progression after leaving relearning at six days: `6d → 18d → 54d → 162d → 486d`. This supplies a gradual route to long intervals without a direct two-day-to-one-year jump.

## 2026-09-03 — Version-one implementation

- The user approved applying the same `<25m / <40m / 3d / 6d` pattern to new cards, although new introductions remain disabled for now.
- Replaced the earlier 2,000-day ceiling with an explicit, editable 3,650-day (ten-year) ceiling, which accommodates the user's preference for four-, five-, or eight-year delays without using Anki's roughly century-scale default.
- Added a self-contained pasteable script at `src/anki-custom-scheduler.js`, installation documentation, and dependency-free Node tests.
- The script is guarded to the `zEK5000` and `Kor to Eng 5000` deck roots, supports normal and rescheduling-filter state shapes, ignores elapsed overdue time, preserves unrelated state fields, and leaves unmatched decks unchanged.
- Seven automated tests pass. Live installation still requires a fresh export, confirmation of the exact live deck name, changing the deck-option maximum interval to 3,650, pasting the whole script into Custom scheduling, and checking displayed intervals before answering.
- Live installation is now complete in both separate Anki accounts. On the first deck, a retained relearning card displayed `25m / 40m / 3d / 6d`, confirming that the custom code executed. The user reported successful completion of the second-deck setup as well.
- Both accounts have verified pre-installation `.colpkg` rollback backups with scheduling included and media intentionally excluded.
- Next action: complete a normal full review session on 2026-09-04, note the displayed choices for ordinary review cards as well as relearning cards, and report any surprising intervals or queue behavior before changing the model further.

## 2026-09-03 — Backup audit

- Verified the two files in `C:\GoogleDrive\My Drive\9b.Non Work Related\Korean Ongoing Study\Anki Backups\20260903` as readable modern `.apkg` deck packages with valid ZIP structure and SQLite integrity.
- Korean-to-English contains 5,179 notes/cards and 243,300 review-log entries; English-to-Korean contains 4,884 notes/cards and 242,851 review-log entries. Their latest review timestamps and counts match the packages previously analyzed.
- Both packages include scheduling/review history, and their media bundles are empty. The user does not want audio preserved; missing audio is therefore intentional and not a backup defect for this project.
- These are deck packages that merge on import, not full collection packages that replace the collection. For an exact pre-scheduler rollback, create a separate full collection export for each account with scheduling information enabled and media disabled. Never import both related collections into the same account because their shared note GUIDs can merge.
- Two later collection packages, `collection-20260903180530.colpkg` and `collection-20260903180620.colpkg`, are structurally valid and include scheduling automatically. Their decompressed collection databases are byte-for-byte identical: both contain only `Kor to Eng 5000`, with 5,179 cards and 273,902 review-log rows.
- One Korean-to-English collection backup is therefore complete, but a full `zEK5000` collection backup is still needed. Switch and fully sync to the English-to-Korean account, confirm the displayed deck name, and export another collection package with media excluded.
- Follow-up verification: the duplicate was removed and replaced with `collection-20260903181114.colpkg`. The folder now contains two distinct, healthy full collection backups: `collection-20260903180620.colpkg` for `Kor to Eng 5000` (5,179 cards; 273,902 review-log rows) and `collection-20260903181114.colpkg` for `zEK5000` (4,884 cards; 301,448 review-log rows). Both pass ZIP and SQLite integrity checks, include scheduling, and intentionally contain no media.

## 2026-09-03 — Review sort-order investigation

- AnkiDroid 2.24 uses Anki backend 25.09.2. In that exact source, `Ascending retrievability` remains valid with FSRS disabled and explicitly uses the legacy SM-2 relative-overdueness expression `(overdue days / stored interval)`, highest relative overdueness first. The menu label is therefore not an FSRS-only mistake.
- On both exported collections, the first 35 cards under ascending retrievability would all be stored one-day cards, with a median of roughly 542 days overdue. This strongly explains the observed concentration on extremely weak short-interval cards.
- `Due date, then random` is not random across the backlog; it prioritizes the oldest due dates and randomizes ties.
- Recommended current setting: `Random` for ordinary review cards. It gives all currently due cards a chance, while the user's 11 learning/relearning carryovers remain separately prioritized by the learning queue. Expected 1–2-day representation in a random 35-card draw is about 17 cards for English-to-Korean and 14 for Korean-to-English, instead of all 35.
- Random does not pull cards that are not yet due. Reconsider due-date ordering once the persistent backlog is under control.

## 2026-09-03 — First live installation check

- The user pasted the standalone script into Custom scheduling on the first live AnkiDroid collection.
- One of the 11 retained relearning cards displayed `25m / 40m / 3d / 6d`, confirming that the script loaded, the deck guard matched, and the post-miss state mutation works on AnkiDroid 2.24.0.
- The user plans to increase Maximum reviews/day from 30 to 35, keep New cards/day at zero, repeat installation on the second account, and sync each account after its settings are saved.

## 2026-09-03 — Deliberate 11-card carryover

- The user deliberately ends each session with exactly 11 difficult cards still in the short learning/relearning queue. These are cards recalled tentatively near the end that must be seen in the next study session; the user intentionally avoids pressing the one-day option because it does not reliably return them promptly.
- A normal next session therefore begins with 11 protected carryovers plus 30 newly selected due cards, for 41 cards in circulation, and ends by selecting the next 11 carryovers.
- This is a third queue class, not part of the proposed 25 recent + 5 backlog allocation. The desired conceptual composition is 11 must-return cards + 25 other recent/current cards + 5 forced backlog cards.
- A standard two-filter deck cannot guarantee all three quotas. Rebuilding a filtered deck may also disturb the user's carefully retained working set, so the earlier 25+5 filtered-deck proposal should not be deployed unchanged.
- Preserve the 11-card workflow while designing an integrated three-lane session mechanism. Custom interval JavaScript alone cannot select or reserve these lanes.

## 2026-09-07 — Positive live result and daily cadence

- The user reports that the custom timing script is working very well in live study.
- The user is committing to reviewing at least a few words every day to work through the existing backlog. Future workload and cap recommendations should therefore consider a frequent low-minimum cadence rather than the earlier once-weekly pattern alone.
- Next action: compare the complete AnkiDroid settings from the `zEK5000` and `Kor to Eng 5000` accounts for consistency with each other and with the deployed scheduler, then recommend only justified adjustments.

## 2026-09-07 — Deck-options screenshot audit

- Reviewed complete deck-option screenshots for both live accounts. Both use 0 new cards/day, 35 reviews/day, FSRS off, all Easy Days set to Normal, a 3,650-day maximum interval, matching legacy advanced factors, and the custom scheduler is visibly present.
- One material inconsistency remains: `Kor to Eng 5000` uses Random review sort order, while `zEK5000` still uses Ascending retrievability. Change `zEK5000` to Random; custom scheduling controls intervals but cannot correct queue selection.
- Native new-card settings remain historically different (`20m 25m`, Easy 2d for `zEK5000`; `20m 40m`, Easy 6d for `Kor to Eng 5000`). With new cards/day at zero these are inactive, and the custom script overrides targeted new/learning choices to `25m / 40m / 3d / 6d` if new cards are later enabled.
- Leech thresholds differ (30 versus 40), but both actions are Tag Only. This affects tagging policy, not suspension or the custom interval formula; no immediate change is required.
- Audio/auto-advance toggles differ, but auto advance is disabled with both delays at zero and those differences do not affect scheduling.
- Screenshots show the same beginning of the custom scheduler in both accounts but not its full contents, so exact script equality cannot be established from the images alone.
- Next action: change and save `zEK5000` review sort order to Random, then audit AnkiDroid's higher-level/global reviewing settings, especially Learn Ahead.

## 2026-09-20 — Shrinking intraday working-set diagnosis

- The user reports that a roughly 15-card learning/relearning set initially cycles in full, then contracts to a handful and sometimes a two-card alternation; pausing for about five minutes restores the full set.
- The custom script is not assigning unequal visible delays: it still writes exactly 25 or 40 minutes to every targeted short answer.
- Anki backend 25.09.2 adds hidden positive fuzz to each applied intraday learning/relearning delay: up to 25%, capped below five minutes. For the current 25- and 40-minute choices, this is 0–4:59 per answer and is not represented by the proposed answer-button interval.
- Intraday learning cards are ordered by their fuzzed due timestamps. When the main queue is empty, the backend tries to avoid an immediate repeat by moving a newly requeued card behind only the next card, not behind the whole working set. Together, those rules can concentrate selection on a small low-due subset or pair while other cards sit a few minutes later.
- The five-minute recovery is evidence that fuzz contributes, but fuzz alone does not explain a stable two-card alternation. Selection is not reshuffled randomly on each draw: the queue remains deterministically ordered by stored due timestamps, and the collapsed-queue reinsertion rule moves an early reanswered card behind only one other card. That rule can reinforce a stable pair.
- A live test verified that the global Learn Ahead value is 80 minutes. Setting it to zero immediately hid all 11 remaining cards behind the completion screen, and restoring 80 made them reappear. This confirms that the working set is being sustained entirely by early review; zero is not a usable solution for the user's workflow.
- Custom-scheduling JavaScript cannot directly select the next card or disable backend fuzz. A more targeted stock-client experiment is an explicit round-robin drill mode: keep Learn Ahead at 80 but use very small short-answer delays such as 1 and 3 seconds. Backend 25.09.2 adds no learning fuzz at those values (`floor(25%)` is zero), and a normally paced answer should put the card after the other already-due cards. This preserves uninterrupted cycling while Good/Easy can still graduate to 3/6 days. It changes the displayed short choices to under one minute and requires isolated testing before live deployment.
- A less direct alternative is to keep minute-scale steps and set Learn Ahead just below the repeatedly used step (for example about 39 minutes for a 40-minute Hard step), forcing a short real pause instead of continuous pair cycling. It cannot provide uninterrupted full-set rotation and will still have up to five minutes of spread.
- Next action: build and simulate a configurable 1-second/3-second drill-mode variant, then test it in an isolated profile or narrowly on one account before considering replacement of the live script.

## 2026-09-20 — Upstream scheduling report

- Posted an anonymized report to the Anki Forums Scheduling category: `https://forums.ankiweb.net/t/relearning-queue-repeatedly-alternates-between-the-same-two-cards/71149`.
- The report describes the full-set-to-subset-to-two-card contraction, the five-minute recovery, the Learn Ahead 80-to-zero experiment, the custom 25/40-minute choices, and the potentially relevant `requeue_learning_entry()` logic.
- The post asks whether the two-card alternation is intended and whether reinserting an answered card at the end of the currently eligible learning set would provide fairer round-robin behavior.
- Next action: monitor maintainer/community responses and provide a more controlled reproduction if requested. Do not change the live scheduler based only on the current hypothesis.

### Forum response and revised conclusion

- A forum response explained that the observed contraction is expected behavior: Learn Ahead only pulls future Learn/Relearn cards when no normally available cards remain, and pulls them in the order in which their actual fuzzed timestamps would become due.
- Even with identical visible steps, cards receive different timestamps because they are answered at different moments and receive short-interval fuzz. After a full pass compresses their answer times, cards at the short end of that ordering can remain ahead of the rest and alternate.
- Treat this as designed behavior rather than an established backend defect. The `requeue_learning_entry()` rule may contribute to avoiding immediate self-repetition, but the due-time ordering is sufficient to explain the observed pair and no upstream code defect has been demonstrated.
- The responder's FSRS suggestion is separate from this queue issue. Do not enable FSRS casually: the current project intentionally uses FSRS off with a custom interval policy, so any migration would require separate analysis and controlled testing.
- Next action: decide whether to accept the five-minute pause or redesign the short-step/Learn Ahead relationship; if continuing on the forum, frame round-robin cycling as a feature request or workflow goal rather than a bug report.

## 2026-09-20 — Possible maintained AnkiDroid fork

- A forum moderator considered the current behavior intentional and opposed fixed-order round-robin repetition on learning-method grounds. The user decided not to press the upstream request further.
- Anki and AnkiDroid are open source, so a private custom build is technically possible. Prefer a narrow fork with one isolated, tested queue-policy patch over a stripped-down rewrite; collection integrity, review history, undo, synchronization, backups, Android lifecycle, and schema compatibility make a replacement app disproportionately risky.
- The desired experimental policy would reinsert an answered early Learn/Relearn card behind the complete eligible working set, ideally with the set shuffled between passes to avoid fixed-sequence cues.
- A fork remains independent when upstream changes: official updates neither delete nor overwrite it, but they also do not arrive automatically. The fork stays based on its old commit until upstream changes are fetched and merged or rebased, the small custom patch is reapplied or adapted, tests pass, and a new APK is built.
- Do not freeze a custom build indefinitely. Missing security fixes, Android compatibility changes, sync changes, or collection-schema changes could eventually make it unsafe. Keep the customization as a small patch that can be carried onto supported upstream releases.
- Safe development sequence if pursued: (1) create a standalone queue simulator reproducing current and proposed behavior, (2) add automated fairness/regression tests, (3) patch the official shared scheduler backend, (4) build a separately named test APK that can coexist with official AnkiDroid, and (5) test only with a disposable profile/account and deck before considering live data.
- No fork, APK, or backend modification has been created yet. This remains a possible future workstream; the first milestone would be the simulator, not a live Android build.

## 2026-09-21 — Two-workstream decision point

- The user is choosing between (1) a maintained Anki/AnkiDroid queue-policy fork for shuffled round-robin Learn Ahead cycling and (2) combining the English-to-Korean and Korean-to-English collections into one account without Anki merging their related notes.
- Re-verified the backup directory `C:\GoogleDrive\My Drive\9b.Non Work Related\Korean Ongoing Study\Anki Backups\20260903`. It still contains the two deck packages and the two distinct full collection packages audited on 2026-09-03.
- The directional deck packages share 4,873 note GUIDs, which is the principal reason importing them together can update/merge notes instead of preserving two independent lists.
- A one-note/two-card-template model is native Anki design, but makes the two directional cards siblings and may introduce sibling-burying interactions. The lower-coupling first experiment is to preserve two independent decks and notes while safely assigning one side new identities in a disposable collection; preservation of scheduling and review history must be proven before any live migration.
- Preliminary priority recommendation: investigate the one-account migration first because it removes recurring logout/sync friction and can be tested offline on copies. It also establishes the eventual collection topology before any custom Android build. The fork remains a separate later workstream, beginning with a simulator.
- Before any live migration, create fresh current full-collection backups from both accounts. Do not modify or combine the September backups in place, and do not import both unmodified related packages into one collection.

## 2026-09-21 — Fresh pre-unification backup, Korean-to-English

- Created `C:\GoogleDrive\My Drive\9b.Non Work Related\Korean Ongoing Study\Anki Backups\20260921-pre-unification` with separate directional-deck subfolders.
- Exported the currently logged-in `Kor to Eng 5000` collection from AnkiDroid 2.24.0 as a full `.colpkg`, scheduling/history included and media excluded. Saved the verified computer copy as `Korean-to-English-Kor-to-Eng-5000\Kor-to-Eng-5000_full-collection_20260921-100600.colpkg`.
- Verification: SHA-256 `58E656EDF03A5C2B94B9EB8F46FF121533DE6F89C5218671DDBEF73CFF80D631`; embedded SQLite integrity `ok`; 5,179 notes; 5,179 cards; 275,355 review-log rows; decks `Default` and `Kor to Eng 5000`.
- During initial UI navigation, a scaled screenshot caused one unintended tap on AnkiDroid's Sync button instead of More options. AnkiDroid reported `Collection synced` with no conflict, overwrite, or replacement prompt; the visible deck and 27-card due count remained unchanged. No import or rescheduling occurred. Subsequent taps used current UI bounds.
- The source export remains in Android Downloads as `collection-20260921100600.colpkg`; do not delete it until both computer-side backups and manifests are complete.

## 2026-09-21 — Fresh pre-unification backup, English-to-Korean

- User-provided account designations: `Kor to Eng 5000` belongs to the **rawforums email account**; `zEK5000` belongs to the **rawaccounts email account**. Full addresses were not recorded.
- Exported the `zEK5000` collection as a full `.colpkg`, scheduling/history included and media excluded. Saved the verified computer copy as `English-to-Korean-zEK5000\zEK5000_full-collection_20260921-101242.colpkg`.
- Verification: SHA-256 `59ED6AB4B3CE0F8368913968E208B01189C8C56983F04743DBA28EED1A67E2B8`; embedded SQLite integrity `ok`; 4,884 notes; 4,884 cards; 303,592 review-log rows; decks `Default` and `zEK5000`.
- Added `20260921-pre-unification\README.md` as a human-readable manifest covering both account aliases, package paths, counts, hashes, export settings, phone-side filenames, and the shared-GUID warning.
- The second source export remains in Android Downloads as `collection-20260921101242.colpkg`. Both verified Google Drive packages must remain unchanged as rollback sources for the isolated migration experiment.

## 2026-09-21 — Backlog progress since September 3

- Recomputed the same active-review due measure directly from both September 3 and September 21 full collection databases, using each collection's own creation timestamp and export-time scheduler day. The method exactly reproduces the earlier 2,904 and 2,979 baselines.
- Korean-to-English: due-review backlog fell from 2,904 to 2,714, a net reduction of 190 (6.5%). Of the old due set, 251 left the due-review backlog (241 scheduled into the future and 10 currently in learning/relearning); 61 other cards entered the due set meanwhile. There were 1,453 review-log events on 420 distinct cards, including 402 cards from the old due set.
- English-to-Korean: due-review backlog fell from 2,979 to 2,848, a net reduction of 131 (4.4%). Of the old due set, 203 left the due-review backlog (193 scheduled into the future and 10 currently in learning/relearning); 72 other cards entered the due set meanwhile. There were 2,144 review-log events on 436 distinct cards, including 424 cards from the old due set.
- Combined: backlog fell from 5,883 to 5,562, a net reduction of 321 (5.5%). The user made 3,597 answer events on 856 distinct cards; 454 old due cards left the due-review backlog while 133 cards newly matured into it.
- The narrower due 1–2-day population fell from 1,148 to 1,020 in Korean-to-English and from 1,410 to 1,183 in English-to-Korean. Combined one-day cards fell from 1,382 to 1,098, and combined one-or-two-day cards fell from 2,558 to 2,203.
- The deck-list display of 17 review cards plus 10 learning cards is the capped/current session queue, not the complete underlying due backlog.
- User clarification: 17 ordinary reviews plus 10 learning/relearning cards is a minimum daily target, not a daily cap or typical maximum. The user reviews substantially more whenever time permits and is trying to meet at least this floor every day. Future workload projections should model a 27-card minimum with variable additional study, not assume a fixed 27-card daily workload.

## 2026-09-21 — Burmese and Thai archival account backup

- The account designated by the user as the **drew3452 email account** contains five non-default decks: `Burmese`, `Pocket Thai Vocab`, `Thai Alphabet`, `Thai Vowels and Vowel Combinations`, and `Thai_Alphabet2`. Full email address was not recorded.
- Exported the complete collection with scheduling/history and media included to `20260921-pre-unification\Spare-account-drew3452-Burmese-and-Thai\drew3452_Burmese-and-Thai_full-collection-with-media_20260921-103137.colpkg`.
- Verification: 126,597,693 bytes; SHA-256 `30E26350809235B7CC2D6DD52EC4030D1741617D390DA622BBE4781E23DF6C2D`; full ZIP test `ok`; embedded SQLite integrity `ok`; 3,150 notes; 5,694 cards; 229,265 review-log rows; 1,180 media objects.
- This is valuable travel-study material, not an empty disposable account. Preserve the live account and verified package. Use only a restored/imported copy in an isolated local profile for destructive or migration testing.
- Updated the backup-folder README with the account designation, deck inventory, verified package details, media distinction, and test-safety warning. The phone-side source remains in Downloads as `collection-20260921103137.colpkg`.

### Individual deck packages

- At the user's request, added `Spare-account-drew3452-Burmese-and-Thai\individual-deck-packages` with separate `.apkg` exports for all five decks. Every export includes scheduling information, its deck preset, and referenced media; older-Anki compatibility mode remained off.
- Verified every archive with a complete ZIP test and SQLite integrity check. For all five decks, card ID sets and current scheduling fields match the corresponding subset of the full collection exactly, and exported review-log counts match all full-collection review rows belonging to those current cards.
- Counts: Burmese 2,500 notes / 5,000 cards / 57 review rows / 11 media objects; Pocket Thai Vocab 515 / 515 / 17 / 514; Thai Alphabet 44 / 44 / 48 / 132; Thai Vowels and Vowel Combinations 47 / 47 / 56 / 81; Thai_Alphabet2 44 / 88 / 41 / 88.
- Added an individual-package README containing filenames, exact byte sizes, SHA-256 hashes, contents, verification status, and restore guidance. Preserve the full `.colpkg` as the authoritative disaster-recovery source because it retains collection-wide historical rows and media outside the current deck subsets.

## 2026-09-21 — Korean collection identity-separation design

- The user intends to use the drew3452 AnkiWeb account as the eventual home for both Korean directional decks, alongside the archived Burmese/Thai decks, if isolated migration tests pass.
- Fresh-database collision audit: the Korean collections share 4,873 note GUIDs, the same 4,873 numeric note IDs, and the same 4,873 card IDs. Renaming decks is insufficient; Anki identifies imported notes by GUID.
- Both directional collections use notetype ID `1076778696` (`Korean Vocab`), but their notetype, field, and template configuration hashes differ. English-to-Korean also has one note using a `Basic` notetype ID that collides with a differently named/configured type in Korean-to-English. For true independence, clone every used notetype in each transformed import and give it a directional name and fresh ID; do not allow either Korean deck to share or update a target-account notetype.
- Review-log identity is a separate collision risk: Korean-to-English and English-to-Korean share 12,296 review-log IDs. Against the drew3452 collection, Korean-to-English collides on 12,296 review-log IDs and English-to-Korean on 227,621. Package import historically inserts review rows by primary-key ID with collision avoidance/ignore behavior, so preserving history requires controlled remapping rather than relying on default import.
- Target design for transformed `.apkg` files: fresh GUIDs for all notes in the transformed directional lineage; fresh numeric note and card IDs with card-to-note references updated; cloned directional notetype IDs with notes remapped; fresh review-log IDs with `cid` updated while preserving review timestamps as closely as possible; unchanged note fields, card ordinal, queue, due, interval, ease, repetitions, lapses, and other scheduling state. Deck names remain `Kor to Eng 5000` and `zEK5000`.
- Do not import either Korean `.colpkg` into drew3452 because collection-package import replaces the current collection. Produce/import `.apkg` deck packages with scheduling instead. Omit conflicting source deck presets during import, then create explicit directional presets in the target and reapply the verified custom scheduler/settings.
- Next milestone: implement a deterministic transformer and invariant tests on copies, create two transformed `.apkg` files, import both into an unsynced disposable local Anki profile containing a copy of drew3452, and verify exact deck/note/card/history/scheduling/template counts and zero cross-deck GUID/notetype collisions before any live-account import.

### Text-only cleanup policy for transformed Korean decks

- The user studies these decks from the text on the two sides and authorizes removal of obsolete pronunciation/audio material in the transformed copies. The verified source backups remain unchanged.
- Read-only field audit found 307 notes containing sound references: 286 in `Kor to Eng 5000` and 21 in `zEK5000`. The packages contain no media objects, so these are dangling references rather than playable audio. No image references were found. Remove the Audio field and its stale sound references from the cloned directional note types.
- Preserve the Korean and English field contents. Existing markup is overwhelmingly structural (`br` and `div`, with a few `i` tags), so retain useful line breaks/emphasis instead of blanket-stripping HTML.
- Preserve Hanja and Number values as hidden note data during the first migration, but exclude them from the simple front/back templates. This keeps the visible cards text-only and uncluttered while avoiding irreversible loss of potentially useful text and ordering metadata.
- `zEK5000` contains one Basic-type outlier with two nonempty plain-text fields and no audio, images, or HTML. Convert it into the cloned English-to-Korean directional note type during transformation rather than retaining a separate Basic notetype.

### Deck, notetype, template, and preset normalization audit

- Use consistent destination deck names `Kor2Eng5000` and `Eng2Kor5000` (pending final package creation). Keep them as separate flat decks rather than parent/child decks so choosing one cannot accidentally study both.
- A deck, note type, card template, and deck-options preset are distinct objects. The migration must allocate fresh IDs and explicit directional names for all four relevant layers instead of relying on names or importer collision behavior.
- Current source assignment: `Kor to Eng 5000` uses preset `Default` (ID 1); `zEK5000` uses preset `EK5000` (ID 1526083197802). The drew3452 destination already has a different `Default` and a different, currently unused `EK5000` with those same IDs/names. Therefore do not reuse or import either source preset under its current identity.
- Create two fresh, directional presets (working names `Kor2Eng5000 Options` and `Eng2Kor5000 Options`) and assign them explicitly. Preserve each source's active behavior for the first migration rather than silently homogenizing settings: K→E has learning steps 20/40 minutes, relearning 25, reviews/day 17, Easy graduation 6 days, leech threshold 40, random review order, max interval 3650; E→K has learning steps 20/25, relearning 25, reviews/day 17, Easy graduation 2 days, leech threshold 30, random review order, max interval 3650. Both use initial ease 2.0, Easy multiplier 2.0, Hard 1.0, interval multiplier 1.0, tag-only leeches, and autoplay disabled.
- The drew3452 account currently has no custom-scheduling script. Both Korean sources contain the same verified 4,635-character script, currently guarded to the old deck names. In the isolated target profile, install one updated collection-global copy guarded only to `Kor2Eng5000` and `Eng2Kor5000`; leave Burmese/Thai decks untouched.
- Create fresh directional note types and one template each. Preserve the current visible text arrangement during first migration: K→E shows Korean, then English plus Hanja; E→K shows English plus Hanja, then Korean. Remove Audio fields/references and keep Number as hidden metadata. The one Basic outlier maps Front→English and Back→Korean into the E→K note type.
- Both source templates contain an obsolete fixed target-deck override (`1353152893425`) that does not identify the present directional decks. Reset the cloned templates' target-deck override to zero/current-deck behavior so cards cannot be generated into an unintended deck.
- Verification gate now includes: each destination deck points to its intended fresh preset; every note points to its intended fresh directional note type; each note type has exactly one correctly named directional template; no template has a fixed deck override; the global custom scheduler names only the two new deck roots; and all Burmese/Thai deck, note-type, preset, card, and history data remain unchanged.

## 2026-09-21 — Korean transformation implementation and paused run

- Added `tools/transform_integrate_korean.py`, using the exact Anki backend version used by AnkiDroid 2.24.0 (`anki==25.9.2`) plus modern-package zstd/media handling. Updated the custom scheduler guard and tests to the normalized names `Kor2Eng5000` and `Eng2Kor5000`; all seven scheduler tests pass and the transformer compiles.
- The transformer verifies the three fixed source SHA-256 hashes, extracts copies only, creates independent directional decks/notetypes/templates/presets, removes Audio, preserves Korean/English/Hanja/Number, converts the Basic outlier, converts day-based due values between collection epochs, remaps linked review history near its original millisecond timestamps, installs the guarded scheduler, sets Learn Ahead to 80 minutes, retains FSRS off, exports two `.apkg` files plus a full media `.colpkg`, and independently reopens/verifies each output.
- Failed exploratory workspaces `v1`–`v3` were intentionally kept separate and produced no finalized package. `v3` exposed that `DeckManager.id(..., type=...)` selects a filtered-deck type rather than a preset; the code was corrected and separately verified to create a normal deck and assign its preset through `deck["conf"]`.
- Per the user's stop instruction, the current corrected run was not restarted after its next failure. The preserved workspace is `tmp/integration-20260921-v4`; its intended output directory is `Korean-integration-test-artifacts-v4` under the 2026-09-21 Google Drive backup root.
- The `v4` run completed both directional transformations, review-ID allocation/insertion, global-setting updates, directional structure checks, and total note/card/review count checks. It then stopped before preservation comparison or package export at `target.db.commit()` because Anki 25.9.2's `DBProxy` has no public `commit()` method; the backend manages transactions itself. No final `.apkg` or `.colpkg` was produced.
- Resume point: remove the unnecessary `target.db.commit()` call, start from pristine backups in a new `v5` workspace/output directory, allow the remaining original-row/media comparisons and exports to run, then inspect the verification report. Do not treat any `v1`–`v4` directory as a deliverable.

### Reassessment after model change — read-only checkpoint audit

- User requested reassessment before further runs. No transformation was restarted. This finding supersedes the recommendation to automatically rebuild from scratch after deleting `.commit()`.
- The closed v4 database passes SQLite integrity. Comparing original destination rows by primary key found zero missing/changed rows across notes (3,150), cards (5,694), revlog (229,265), decks, presets, notetypes, fields, and templates. Integrated totals are 13,213 notes, 15,757 cards, and 719,013 review rows.
- Independently reconstructed source-to-destination mapping from deterministic GUIDs for all 5,179 K→E and 4,884 E→K cards. Type, queue, interval, ease, repetitions, lapses, learning steps remaining, original due/deck, flags, custom data, and non-new due dates match the intended epoch conversion. Per-card linked history counts and answer contents/order match; maximum timestamp displacement is 0 ms K→E and 5 ms E→K.
- Text differs bytewise on 126 K→E and 120 E→K notes, entirely explained by Anki NFC Unicode normalization; no other field-content differences found after planned field mapping. Future validation must explicitly allow only this documented equivalence.
- The previous repeated commentary attributing long runtime to note generation was unsupported: no phase instrumentation existed. Installed DBProxy exposes `transact()`, and the transformer performs large direct SQL batches without an explicit transaction. Measure stages and inspect transaction behavior before claiming a runtime cause or repeating a full run.
- Validation gaps: no actual exported-package import/reimport test; no rendering or scheduler-answer check in integrated collection; no explicit timestamp-drift bound; original-row digest depends on unspecified SQL row order; SQLite comparison attempts to open a second connection while backend owns the database; collection-wide Learn Ahead/other option changes can affect Burmese/Thai behavior despite their stored rows remaining unchanged. Source orphan review rows remain in full backups, while transformed decks deliberately retain only history linked to existing cards.
- Recommended next work: validate and copy the v4 checkpoint, repair transaction/lifecycle handling and add phase logging plus a tiny end-to-end fixture, then export and test real import/reimport in another isolated target copy. A full rebuild is conditional on checkpoint validation, not mandatory. Live deployment still awaits verified packages and explicit account operation authorization.

### Transformation and offline integration completed

- Continued from a copy of the validated v4 checkpoint, with stage logging and independent source/destination comparisons. Added `tools/finish_integration.py` and `tools/check_integrated_scheduler.py`. Fixed the original transformer's direct SQL batches to use `DBProxy.transact()`, replaced nonexistent manual commit with close/reopen around independent SQLite reads, and made row hashing deterministic by primary key. These original-transformer changes compile but were not used to rebuild the successful checkpoint.
- The first actual export/import comparison detected only JSON serialization differences in card `data`; verification now compares parsed JSON contents. v6 then completed source comparison, all-card backend rendering, actual package import into a pristine destination copy, a second import, and full media collection export/readback. Full-data tests superseded the proposed tiny fixture for this recovery.
- Verified artifacts are in `C:\GoogleDrive\My Drive\9b.Non Work Related\Korean Ongoing Study\Anki Backups\20260921-pre-unification\Korean-integration-verified-v6`: `Kor2Eng5000.apkg`, `Eng2Kor5000.apkg`, `drew3452-integrated-TEST-ONLY.colpkg`, the renamed-deck custom scheduler, README, and verification JSON with hashes. The full collection is a TEST ONLY replacement snapshot; use the two additive packages for eventual live installation.
- K→E: 5,179 cards and 244,753 linked reviews; E→K: 4,884 cards and 244,995 linked reviews. All content (allowing NFC normalization), card scheduling fields, absolute due-date conversion, new-card relative order, tags, flags, custom data, and linked history counts/contents/order passed independent comparison. Review timestamp shifts are at most 5ms. Source orphan histories remain in original full backups.
- Integrated totals: 13,213 notes, 15,757 cards, 719,013 review rows. All original destination rows in eight audited tables and all 1,180 media files are preserved. Reimport produced no duplicates or changes to existing audited rows; totals remain exact. Directional preset behavioral settings match their sources; only identity/name/modification metadata differ.
- All 10,063 Korean cards rendered successfully before and after actual import, and sentinel rendering proved both directions. Seven scheduler unit tests pass. The installed script also passed 21 real backend state samples spanning all seven decks; Korean intervals matched the policy and non-Korean states were unchanged. No phone UI or sync test has occurred.
- Global settings caveat is explicit in the delivered README: Learn Ahead becomes 80 minutes (target previously 20); other shared options are also set at collection level. These can affect Burmese/Thai queue behavior despite preserved records. The interval script alone is scoped to Korean. Deck packages do not install the global custom script; install the provided JS separately.
- Live phone/accounts and original backups were not modified. Next step is live installation after checking backup freshness; do not overwrite newer study progress with the September 21 snapshot. The original v4 and prior partial folders are retained, not deliverables.

### Live installation preparation — extra destination backup

- User confirms no Korean study since the source backups; verified v6 packages are current. User authorizes removing the five archived Burmese/Thai decks from drew3452 for the Korean installation.
- Saved an additional full media export alongside the earlier drew3452 backup: `Spare-account-drew3452-Burmese-and-Thai/drew3452_Burmese-and-Thai_pre-install-with-media_20260921-123145.colpkg` under the existing Google Drive backup root. Size 126,597,693 bytes; phone/local SHA-256 both `99303C498E20AD6A41EAE9F15D4916C06CE8A2BE5BE605744A6506227EBFA738`; complete ZIP test passed. Cloud synchronization not independently confirmed.
- Phone is back at the five-deck list. No decks deleted and no Korean packages or global scheduler installed yet. Next: verify destination account, remove only the five authorized decks, import both v6 packages with scheduling/presets, install guarded global JS, verify without grading cards, then sync.

### Live installation performed — sync in progress

- Reconfirmed drew3452 in AnkiDroid Sync settings. With renewed explicit authorization, removed exactly the five archived Burmese/Thai decks (5,694 cards total); all full and per-deck backups remain intact.
- Imported both verified v6 `.apkg` files with learning progress and deck presets enabled. Both decks are visible, each with 0 new / 10 learning / 17 review currently offered. No review answers were submitted; the displayed 9 studies today come from imported history.
- Installed the original tested scheduler via AnkiDroid's USB WebView connection, saved and reopened the editor, and verified exact source equality after newline normalization (4,636 characters). Initial keyboard-based entry was altered by the IME and discarded without saving. Seven scheduler unit tests pass.
- Learn Ahead set to 80 minutes. Both live deck directions checked with Show Answer only; learning buttons show 25m/40m/3d/6d. Temporary HTML/JavaScript debugging turned off and verified; developer options disabled; local ADB port forward removed.
- Sync started and is uploading the large preserved review history. Completion not yet confirmed. Phone UI helper now rejects failed UI dumps instead of returning stale state.
- Upload reached 448,744 added/modified records without error before the phone auto-locked at about 13:03. Asked user to unlock; do not claim completed sync yet. Final read-back export remains pending. `tools/verify_phone_export.py` is prepared and compiles; it compares a new exported snapshot with the original Korean sources and checks counts, settings, presets, and all-card rendering on a local copy.

### Final phone read-back verified — all clear

- At about 13:23, two sync checks returned `Collection synced. Media is being synced in the background.` The collection sync is confirmed complete; separate media completion was not asserted. These Korean decks are text-only and have no required media.
- Exported the installed phone collection without media and ran `tools/verify_phone_export.py` successfully on a local extracted copy. All 10,063 cards/notes, scheduling fields, absolute due dates, new-card ordering, content, tags, and 489,748 linked reviews match the original Korean backups under the previously documented identity remapping, NFC normalization, and maximum 5ms history timestamp shift. No cards graded during checks.
- All 10,063 cards rendered successfully; both directional templates and independent presets verified. Saved custom scheduler matches source exactly, Learn Ahead is 80 minutes, FSRS is off, and all preset behavior matches the verified baseline. All five old decks are absent.
- Saved the 21,873,694-byte phone export to `Korean-integration-verified-v6/drew3452_Korean-installed-verified_no-media_20260921-132301.colpkg` under the existing Google Drive backup root (cloud file sync not independently checked). Local verification directory: `tmp/phone-readback-20260921-132301`. Phone may be unplugged; user can begin normal AnkiDroid study. Round-robin queue changes remain a separate future project.
