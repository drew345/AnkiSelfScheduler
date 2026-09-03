(() => {
    "use strict";

    // This entire file is pasted into Anki's Custom scheduling box.
    const CONFIG = Object.freeze({
        targetDeckRoots: ["zEK5000", "Kor to Eng 5000"],
        againMinutes: 25,
        hardMinutes: 40,
        relearningGoodDays: 3,
        relearningEasyDays: 6,
        minimumReviewBaseDays: 2,
        hardMultiplier: 0.8,
        goodMultiplier: 1.8,
        easyMultiplier: 3.0,
        maximumIntervalDays: 3650,
    });

    if (typeof states !== "object" || states === null ||
        typeof ctx !== "object" || ctx === null) {
        return;
    }

    const deckName = typeof ctx.deckName === "string" ? ctx.deckName : "";
    const isTargetDeck = CONFIG.targetDeckRoots.some(
        (root) => deckName === root || deckName.startsWith(`${root}::`),
    );

    // Custom scheduling is global, so leave every unmatched deck untouched.
    if (!isTargetDeck) {
        return;
    }

    function originalState(answerState) {
        return answerState?.normal ??
            answerState?.filtered?.rescheduling?.originalState ??
            null;
    }

    function replaceOriginalState(answerState, replacement) {
        if (answerState?.normal) {
            answerState.normal = replacement;
            return true;
        }
        if (answerState?.filtered?.rescheduling?.originalState) {
            answerState.filtered.rescheduling.originalState = replacement;
            return true;
        }
        return false;
    }

    function reviewPart(normalState) {
        return normalState?.review ?? normalState?.relearning?.review ?? null;
    }

    function learningPart(normalState) {
        return normalState?.learning ?? normalState?.relearning?.learning ?? null;
    }

    function boundedDays(days) {
        return Math.max(1, Math.min(CONFIG.maximumIntervalDays, Math.ceil(days)));
    }

    function setLearningDelay(answerState, minutes) {
        const learning = learningPart(originalState(answerState));
        if (learning) {
            learning.scheduledSecs = minutes * 60;
            return true;
        }
        return false;
    }

    function setReviewInterval(answerState, days) {
        const review = originalState(answerState)?.review;
        if (!review) {
            return false;
        }
        review.scheduledDays = boundedDays(days);
        return true;
    }

    // Good may ordinarily lead to another learning step. For this scheduler,
    // Good and Easy graduate immediately, so Easy's review state is the template.
    function forceGraduation(answerState, days, templateState) {
        const existingReview = originalState(answerState)?.review;
        if (existingReview) {
            existingReview.scheduledDays = boundedDays(days);
            return true;
        }

        const templateReview = reviewPart(originalState(templateState));
        if (!templateReview) {
            return false;
        }

        return replaceOriginalState(answerState, {
            review: {
                ...templateReview,
                scheduledDays: boundedDays(days),
            },
        });
    }

    function ordinaryReviewIntervals(previousScheduledDays) {
        const parsed = Number(previousScheduledDays);
        const base = Number.isFinite(parsed)
            ? Math.max(CONFIG.minimumReviewBaseDays, parsed)
            : CONFIG.minimumReviewBaseDays;

        const hard = boundedDays(CONFIG.hardMultiplier * base);
        const good = boundedDays(Math.max(hard + 1, CONFIG.goodMultiplier * base));
        const easy = boundedDays(Math.max(good + 1, CONFIG.easyMultiplier * base));
        return { hard, good, easy };
    }

    const current = originalState(states.current);
    if (!current) {
        return;
    }

    if (current.review) {
        const intervals = ordinaryReviewIntervals(current.review.scheduledDays);

        // Again enters the existing 25-minute relearning step.
        setLearningDelay(states.again, CONFIG.againMinutes);
        setReviewInterval(states.hard, intervals.hard);
        setReviewInterval(states.good, intervals.good);
        setReviewInterval(states.easy, intervals.easy);
        return;
    }

    if (current.new || current.learning || current.relearning) {
        setLearningDelay(states.again, CONFIG.againMinutes);
        setLearningDelay(states.hard, CONFIG.hardMinutes);
        forceGraduation(
            states.good,
            CONFIG.relearningGoodDays,
            states.easy,
        );
        forceGraduation(
            states.easy,
            CONFIG.relearningEasyDays,
            states.easy,
        );
    }
})();
