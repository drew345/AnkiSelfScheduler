const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const schedulerCode = fs.readFileSync(
    path.join(__dirname, "..", "src", "anki-custom-scheduler.js"),
    "utf8",
);

function review(days, elapsedDays = 0) {
    return {
        scheduledDays: days,
        elapsedDays,
        easeFactor: 1.3,
        lapses: 4,
        leeched: false,
    };
}

function learning(seconds = 1200) {
    return { remainingSteps: 1, scheduledSecs: seconds, elapsedSecs: 0 };
}

function reviewStates(days, elapsedDays = 0) {
    return {
        current: { normal: { review: review(days, elapsedDays) } },
        again: {
            normal: {
                relearning: {
                    review: review(1, elapsedDays),
                    learning: learning(1500),
                },
            },
        },
        hard: { normal: { review: review(days) } },
        good: { normal: { review: review(days) } },
        easy: { normal: { review: review(days) } },
    };
}

function newStates() {
    return {
        current: { normal: { new: { position: 1 } } },
        again: { normal: { learning: learning(1200) } },
        hard: { normal: { learning: learning(1350) } },
        good: { normal: { learning: learning(1500) } },
        easy: { normal: { review: review(2) } },
    };
}

function relearningStates() {
    return {
        current: {
            normal: {
                relearning: { review: review(1), learning: learning(1500) },
            },
        },
        again: {
            normal: {
                relearning: { review: review(1), learning: learning(1500) },
            },
        },
        hard: {
            normal: {
                relearning: { review: review(1), learning: learning(2250) },
            },
        },
        good: { normal: { review: review(1) } },
        easy: { normal: { review: review(2) } },
    };
}

function run(states, deckName = "zEK5000") {
    vm.runInNewContext(schedulerCode, {
        states,
        ctx: { deckName, seed: 1 },
    });
    return states;
}

function intervals(states) {
    return [
        states.hard.normal.review.scheduledDays,
        states.good.normal.review.scheduledDays,
        states.easy.normal.review.scheduledDays,
    ];
}

test("one- and two-day cards use the two-day minimum base", () => {
    assert.deepEqual(intervals(run(reviewStates(1))), [2, 4, 6]);
    assert.deepEqual(intervals(run(reviewStates(2))), [2, 4, 6]);
});

test("ordinary intervals use 0.8x, 1.8x, and 3x with ceiling rounding", () => {
    assert.deepEqual(intervals(run(reviewStates(6))), [5, 11, 18]);
    assert.deepEqual(intervals(run(reviewStates(18))), [15, 33, 54]);
});

test("elapsed overdue time does not change the result", () => {
    assert.deepEqual(intervals(run(reviewStates(6, 10))), [5, 11, 18]);
    assert.deepEqual(intervals(run(reviewStates(6, 500))), [5, 11, 18]);
});

test("new cards use 25m, 40m, 3d, and 6d", () => {
    const states = run(newStates());
    assert.equal(states.again.normal.learning.scheduledSecs, 25 * 60);
    assert.equal(states.hard.normal.learning.scheduledSecs, 40 * 60);
    assert.equal(states.good.normal.review.scheduledDays, 3);
    assert.equal(states.easy.normal.review.scheduledDays, 6);
});

test("relearning cards use 25m, 40m, 3d, and 6d", () => {
    const states = run(relearningStates());
    assert.equal(states.again.normal.relearning.learning.scheduledSecs, 25 * 60);
    assert.equal(states.hard.normal.relearning.learning.scheduledSecs, 40 * 60);
    assert.equal(states.good.normal.review.scheduledDays, 3);
    assert.equal(states.easy.normal.review.scheduledDays, 6);
});

test("unmatched decks are unchanged", () => {
    const states = reviewStates(6, 500);
    const before = JSON.stringify(states);
    run(states, "Unrelated Deck");
    assert.equal(JSON.stringify(states), before);
});

test("intervals are capped at ten years", () => {
    assert.deepEqual(intervals(run(reviewStates(3000))), [2400, 3650, 3650]);
});
