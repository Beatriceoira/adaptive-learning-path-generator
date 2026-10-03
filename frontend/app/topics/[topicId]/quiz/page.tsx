"use client";

import { useEffect, useRef, useState } from "react";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, getNextQuizQuestion, getTopic, submitQuizAnswer } from "@/lib/api";
import type { QuizNextResponse, QuizSubmitResponse, Topic } from "@/lib/types";
import { Badge, Button, ErrorState, LoadingState, MasteryBar, Panel, difficultyLabel } from "@/components/ui";

export default function QuizPage({ params }: { params: { topicId: string } }) {
  const { topicId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();

  const [topic, setTopic] = useState<Topic | null>(null);
  const [question, setQuestion] = useState<QuizNextResponse | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState("");
  const [feedback, setFeedback] = useState<QuizSubmitResponse | null>(null);
  const [questionStartedAt, setQuestionStartedAt] = useState<number | null>(null);
  const [stats, setStats] = useState({ answered: 0, correct: 0 });
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  // Which topic the first question has already been requested for. In dev,
  // React Strict Mode runs effects twice on mount; without this guard the
  // page would ask for its first question twice, and if the question bank is
  // exhausted that can mean two separate LLM generation calls.
  const firstLoadFor = useRef<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getTopic(topicId)
      .then((t) => {
        if (!cancelled) setTopic(t);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [token, topicId]);

  useEffect(() => {
    if (!token || firstLoadFor.current === topicId) return;
    firstLoadFor.current = topicId;
    loadNextQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, topicId]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  async function loadNextQuestion() {
    if (!token) return;
    setError(null);
    setIsBusy(true);
    try {
      const q = await getNextQuizQuestion(token, topicId);
      setQuestion(q);
      setSelectedAnswer("");
      setFeedback(null);
      setQuestionStartedAt(Date.now());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the next question.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSubmit() {
    if (!token || !question) return;
    setError(null);
    setIsBusy(true);
    try {
      const responseTimeSeconds = questionStartedAt ? (Date.now() - questionStartedAt) / 1000 : undefined;
      const res = await submitQuizAnswer(token, question.question_id, selectedAnswer, responseTimeSeconds);
      setFeedback(res);
      setStats((prev) => ({ answered: prev.answered + 1, correct: prev.correct + (res.is_correct ? 1 : 0) }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't submit your answer.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-baseline justify-between gap-4">
        <h1 className="text-3xl">{topic?.name ?? "Practice"}</h1>
        {stats.answered > 0 && (
          <p className="shrink-0 text-sm text-ink-muted">
            {stats.correct}/{stats.answered} correct this session
          </p>
        )}
      </div>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
          {!question && (
            <Button variant="secondary" className="mt-3" onClick={loadNextQuestion} disabled={isBusy}>
              Try again
            </Button>
          )}
        </div>
      )}

      {isBusy && !question && (
        <div className="mt-6">
          <LoadingState label="Finding your next question…" />
        </div>
      )}

      {question && !feedback && (
        <Panel className="mt-6">
          <div className="flex items-center gap-2">
            <Badge>{difficultyLabel(question.difficulty_level)}</Badge>
            {question.freshly_generated && <Badge tone="accent">New question</Badge>}
          </div>
          <p className="mt-3">{question.prompt}</p>

          {question.choices ? (
            <div role="radiogroup" aria-label={question.prompt} className="mt-4 space-y-2">
              {question.choices.map((choice) => (
                <label key={choice} className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="quiz-answer"
                    value={choice}
                    checked={selectedAnswer === choice}
                    onChange={() => setSelectedAnswer(choice)}
                  />
                  {choice}
                </label>
              ))}
            </div>
          ) : (
            <input
              type="text"
              aria-label="Your answer"
              value={selectedAnswer}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              className="mt-4 w-full rounded-md border border-line bg-paper px-3 py-2 text-sm"
              placeholder="Your answer"
            />
          )}

          <Button className="mt-5" onClick={handleSubmit} disabled={!selectedAnswer.trim() || isBusy}>
            {isBusy ? "Submitting…" : "Submit answer"}
          </Button>
        </Panel>
      )}

      {feedback && (
        <Panel className="mt-6">
          <p role="status" className={feedback.is_correct ? "text-sage-deep" : "text-rust"}>
            {feedback.is_correct ? "Correct" : "Not quite"}
          </p>
          {!feedback.is_correct && (
            <p className="mt-1 text-sm text-ink-muted">Correct answer: {feedback.correct_answer}</p>
          )}
          {feedback.explanation && <p className="mt-2 text-sm text-ink-muted">{feedback.explanation}</p>}

          <div className="mt-4">
            <p className="text-xs text-ink-muted">Mastery on this topic</p>
            <div className="mt-1">
              <MasteryBar value={feedback.mastery_probability} />
            </div>
          </div>

          <Button className="mt-5" onClick={loadNextQuestion} disabled={isBusy}>
            {isBusy ? "Loading…" : "Next question"}
          </Button>
        </Panel>
      )}
    </div>
  );
}
