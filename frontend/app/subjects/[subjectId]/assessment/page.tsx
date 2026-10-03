"use client";

import { useState } from "react";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, startAssessment, submitAssessment } from "@/lib/api";
import type { AssessmentQuestion, AssessmentSubmitResponse } from "@/lib/types";
import { Button, ErrorState, LinkButton, LoadingState, MasteryBar, Panel } from "@/components/ui";

type Phase = "intro" | "in_progress" | "results";

export default function AssessmentPage({ params }: { params: { subjectId: string } }) {
  const { subjectId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();

  const [phase, setPhase] = useState<Phase>("intro");
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<AssessmentSubmitResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  async function handleStart() {
    if (!token) return;
    setError(null);
    setIsBusy(true);
    try {
      const res = await startAssessment(token, subjectId);
      setAssessmentId(res.assessment_id);
      setQuestions(res.questions);
      setAnswers({});
      setPhase("in_progress");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start the assessment.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSubmit() {
    if (!token || !assessmentId) return;
    setError(null);
    setIsBusy(true);
    try {
      const answerList = questions.map((q) => ({ question_id: q.id, user_answer: answers[q.id] ?? "" }));
      const res = await submitAssessment(token, assessmentId, answerList);
      setResults(res);
      setPhase("results");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't submit your answers.");
    } finally {
      setIsBusy(false);
    }
  }

  const allAnswered = questions.length > 0 && questions.every((q) => (answers[q.id] ?? "").trim().length > 0);

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl">Diagnostic assessment</h1>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      {phase === "intro" && (
        <Panel className="mt-6">
          <p className="text-ink-muted">
            A handful of questions across this subject&apos;s starting topics. There&apos;s no time limit, and this
            just sets your baseline, which keeps adjusting as you practice.
          </p>
          <Button className="mt-5" onClick={handleStart} disabled={isBusy}>
            {isBusy ? "Starting…" : "Start diagnostic"}
          </Button>
        </Panel>
      )}

      {phase === "in_progress" && (
        <div className="mt-6 space-y-6">
          {questions.map((q, i) => (
            <Panel key={q.id}>
              <p className="text-sm text-ink-muted">Question {i + 1}</p>
              <p className="mt-1">{q.prompt}</p>
              {q.choices ? (
                <div role="radiogroup" aria-label={q.prompt} className="mt-4 space-y-2">
                  {q.choices.map((choice) => (
                    <label key={choice} className="flex items-center gap-2 text-sm">
                      <input
                        type="radio"
                        name={q.id}
                        value={choice}
                        checked={answers[q.id] === choice}
                        onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: choice }))}
                      />
                      {choice}
                    </label>
                  ))}
                </div>
              ) : (
                <input
                  type="text"
                  aria-label={`Answer for question ${i + 1}`}
                  value={answers[q.id] ?? ""}
                  onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                  className="mt-4 w-full rounded-md border border-line bg-paper px-3 py-2 text-sm"
                  placeholder="Your answer"
                />
              )}
            </Panel>
          ))}
          <Button onClick={handleSubmit} disabled={!allAnswered || isBusy}>
            {isBusy ? "Submitting…" : "Submit answers"}
          </Button>
        </div>
      )}

      {phase === "results" && results && (
        <div className="mt-6 space-y-6">
          <Panel>
            <p className="text-sm text-ink-muted">Overall score</p>
            <p className="font-display text-3xl">{Math.round(results.overall_score * 100)}%</p>
          </Panel>
          <div className="space-y-3">
            {results.topic_results.map((tr) => (
              <Panel key={tr.topic_id}>
                <div className="flex items-center justify-between">
                  <h3>{tr.topic_name}</h3>
                  <span className="text-sm text-ink-muted">
                    {tr.correct}/{tr.total} correct
                  </span>
                </div>
                <div className="mt-3">
                  <MasteryBar value={tr.mastery_probability} />
                </div>
              </Panel>
            ))}
          </div>
          <div className="flex gap-4">
            <LinkButton href={`/subjects/${subjectId}/roadmap`}>Build my roadmap</LinkButton>
            <LinkButton href={`/subjects/${subjectId}`} variant="secondary">
              Back to subject
            </LinkButton>
          </div>
        </div>
      )}
    </div>
  );
}
