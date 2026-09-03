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
