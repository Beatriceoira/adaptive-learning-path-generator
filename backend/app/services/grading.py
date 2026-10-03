from app.models import QuizQuestion


def grade_answer(question: QuizQuestion, user_answer: str) -> bool:
    """
    Multiple choice / short answer: case-insensitive, whitespace-trimmed exact
    match against the stored correct_answer. Code questions aren't auto-graded
    yet (phase 5 concern) -- treated as incorrect until that lands.
    """
    if question.question_type == "code":
        return False
    return user_answer.strip().casefold() == question.correct_answer.strip().casefold()
