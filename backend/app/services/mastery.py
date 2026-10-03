"""
Mastery tracking via Bayesian Knowledge Tracing (BKT).

BKT models P(L) = probability the learner has mastered a topic, and updates
it after every observed answer using two "noise" parameters:
  - slip:  P(wrong answer | topic is mastered)      -- careless mistakes
  - guess: P(correct answer | topic is NOT mastered) -- lucky guesses
and one "growth" parameter:
  - p_learn: P(transitions from not-mastered to mastered after this
    interaction) -- set to 0 for a diagnostic (a single quiz answer doesn't
    teach anything), and > 0 for practice/study interactions in phase 5.

This is intentionally simple (no training data required) and is the same
update rule the diagnostic (phase 3) and adaptive quiz engine (phase 5)
both call. `apply_answer` also maintains the weak-topic flag (phase 6)
as a side effect, since it's the single place mastery state changes.
"""

from sqlalchemy.orm import Session

from app.models import MasteryScore

DEFAULT_PRIOR = 0.3   # P(L) assumed before any evidence for a topic
DEFAULT_SLIP = 0.1
DEFAULT_GUESS = 0.25
DEFAULT_P_LEARN = 0.15

# Weak-topic detection (phase 6): flagged once there's enough evidence to
# trust the signal (attempts_count threshold) and mastery is still low
# (mastery_probability cutoff). Deliberately simple -- swap for an IRT-based
# rule later without changing anything that reads `is_weak_topic`.
WEAK_TOPIC_MIN_ATTEMPTS = 5
WEAK_TOPIC_MASTERY_CUTOFF = 0.5


def bkt_update(
    prior_mastery: float,
    is_correct: bool,
    slip: float = DEFAULT_SLIP,
    guess: float = DEFAULT_GUESS,
    p_learn: float = DEFAULT_P_LEARN,
) -> float:
    """Returns the posterior P(L) after observing one answer."""
    if is_correct:
        numerator = prior_mastery * (1 - slip)
        denominator = numerator + (1 - prior_mastery) * guess
    else:
        numerator = prior_mastery * slip
        denominator = numerator + (1 - prior_mastery) * (1 - guess)

    posterior = numerator / denominator if denominator > 0 else prior_mastery
    # Learning transition: even if not yet mastered, the interaction may have taught them something.
    posterior_after_learning = posterior + (1 - posterior) * p_learn
    return min(max(posterior_after_learning, 0.0), 1.0)


def get_or_create_mastery(db: Session, user_id: str, topic_id: str) -> MasteryScore:
    mastery = (
        db.query(MasteryScore)
        .filter(MasteryScore.user_id == user_id, MasteryScore.topic_id == topic_id)
        .first()
    )
    if mastery is None:
        mastery = MasteryScore(
            user_id=user_id,
            topic_id=topic_id,
            mastery_probability=DEFAULT_PRIOR,
            attempts_count=0,
            correct_count=0,
        )
        db.add(mastery)
        db.flush()
    return mastery


def recompute_weak_flag(mastery: MasteryScore) -> None:
    """
    Recomputes is_weak_topic from the mastery row's current counters.
    Pure function of already-stored fields, so it's always safe to re-run --
    exposed separately (not just inlined in apply_answer) so a future
    backfill job or admin tool can re-derive it without duplicating the rule.
    """
    mastery.is_weak_topic = (
        mastery.attempts_count >= WEAK_TOPIC_MIN_ATTEMPTS
        and mastery.mastery_probability < WEAK_TOPIC_MASTERY_CUTOFF
    )


def apply_answer(
    db: Session,
    user_id: str,
    topic_id: str,
    is_correct: bool,
    p_learn: float = DEFAULT_P_LEARN,
) -> MasteryScore:
    """
    Records one answered question against a topic's running mastery score:
    updates P(L) via BKT, increments the attempt/correct counters, and
    refreshes the weak-topic flag. Does not commit -- caller controls the
    transaction. This is the only place mastery_probability and
    attempts_count change, so recomputing is_weak_topic here (rather than at
    each call site) keeps it impossible for the flag to drift out of sync
    with the counters it's derived from.
    """
    mastery = get_or_create_mastery(db, user_id, topic_id)
    mastery.mastery_probability = bkt_update(
        mastery.mastery_probability, is_correct, p_learn=p_learn
    )
    mastery.attempts_count += 1
    if is_correct:
        mastery.correct_count += 1
    recompute_weak_flag(mastery)
    return mastery
