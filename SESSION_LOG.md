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

## 2026-09-03 — Deliberate 11-card carryover

- The user deliberately ends each session with exactly 11 difficult cards still in the short learning/relearning queue. These are cards recalled tentatively near the end that must be seen in the next study session; the user intentionally avoids pressing the one-day option because it does not reliably return them promptly.
- A normal next session therefore begins with 11 protected carryovers plus 30 newly selected due cards, for 41 cards in circulation, and ends by selecting the next 11 carryovers.
- This is a third queue class, not part of the proposed 25 recent + 5 backlog allocation. The desired conceptual composition is 11 must-return cards + 25 other recent/current cards + 5 forced backlog cards.
- A standard two-filter deck cannot guarantee all three quotas. Rebuilding a filtered deck may also disturb the user's carefully retained working set, so the earlier 25+5 filtered-deck proposal should not be deployed unchanged.
- Preserve the 11-card workflow while designing an integrated three-lane session mechanism. Custom interval JavaScript alone cannot select or reserve these lanes.
