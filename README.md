# AnkiSelfScheduler

A self-contained custom scheduling script for AnkiDroid 2.24.0 and Anki's v3 scheduler with FSRS disabled.

## Current behavior

For new, learning, and relearning cards:

```text
Again: 25 minutes
Hard:  40 minutes
Good:  3 days
Easy:  6 days
```

For ordinary review cards, `X` is the card's previously assigned interval, with a minimum calculation base of two days:

```text
Again: enter 25-minute relearning
Hard:  ceil(0.8 × X)
Good:  ceil(1.8 × X)
Easy:  ceil(3.0 × X)
```

Elapsed and overdue time are deliberately ignored. Intervals are capped at 3,650 days (ten years).

## Installation

1. Make a fresh `.apkg` backup before changing scheduling.
2. Confirm that FSRS is disabled and scheduler v3 is enabled.
3. In Deck Options, open **Advanced → Custom scheduling**.
4. Remove any prior custom-scheduling code.
5. Paste the complete contents of `src/anki-custom-scheduler.js` into the box.
6. Set the deck's **Maximum interval** option to `3650` days so it agrees with the script.
7. Confirm the answer times on a few cards before committing to a rating.

The pasted code is self-contained. AnkiDroid does not load `package.json`, the test file, or any other repository file.

## Deck guard

Custom scheduling is global. The script acts only on these exact deck roots and their subdecks:

- `zEK5000`
- `Kor to Eng 5000`

If either live deck has a different name, update `targetDeckRoots` before installation. Unmatched decks are left unchanged.

## Testing

With Node.js installed:

```powershell
npm test
```

The automated tests validate state manipulation and interval arithmetic. Learning effectiveness is evaluated only through genuine reviews of the user's live vocabulary collection.

## Scope

This version changes answer-button timing only. It does not rearrange the existing backlog or implement the postponed 11 + 25 + 5 session-selection system.
