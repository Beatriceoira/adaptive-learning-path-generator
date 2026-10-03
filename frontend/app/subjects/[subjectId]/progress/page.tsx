"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, getProgressHistory, getProgressOverview } from "@/lib/api";
import type { ProgressHistory, ProgressOverview } from "@/lib/types";
import { ActivityChart } from "@/components/ActivityChart";
import { Badge, ErrorState, LoadingState, MasteryBar, Panel } from "@/components/ui";

const HISTORY_DAYS = 30;

export default function ProgressPage({ params }: { params: { subjectId: string } }) {
  const { subjectId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();

  const [overview, setOverview] = useState<ProgressOverview | null>(null);
  const [history, setHistory] = useState<ProgressHistory | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    Promise.all([getProgressOverview(token, subjectId), getProgressHistory(token, subjectId, HISTORY_DAYS)])
      .then(([o, h]) => {
        if (cancelled) return;
        setOverview(o);
        setHistory(h);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't load your progress.");
      });
    return () => {
      cancelled = true;
    };
  }, [token, subjectId]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl">Progress</h1>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}
      {!overview && !error && (
        <div className="mt-6">
          <LoadingState label="Loading your progress…" />
        </div>
      )}

      {overview && (
        <div className="mt-6 space-y-8">
          <Panel>
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-5">
              <Stat label="Topics mastered" value={`${overview.topics_mastered}/${overview.topics_total}`} />
              <Stat
                label="Overall accuracy"
                value={overview.overall_accuracy !== null ? `${Math.round(overview.overall_accuracy * 100)}%` : "—"}
              />
              <Stat label="Questions answered" value={String(overview.total_attempts)} />
              <Stat label="Needs attention" value={String(overview.weak_topic_count)} />
              {overview.roadmap_completion_pct !== null && (
                <Stat label="Roadmap complete" value={`${Math.round(overview.roadmap_completion_pct * 100)}%`} />
              )}
            </div>
          </Panel>

          {history && (
            <section>
              <h2 className="text-xl">Last {HISTORY_DAYS} days</h2>
              <Panel className="mt-4">
                <ActivityChart data={history.daily_activity} />
              </Panel>
            </section>
          )}

          <section>
            <h2 className="text-xl">Mastery by topic</h2>
            <div className="mt-4 space-y-3">
              {overview.topic_mastery.map((tm) => (
                <Panel key={tm.topic_id}>
                  <div className="flex items-center justify-between gap-3">
                    <h3>{tm.topic_name}</h3>
                    {tm.is_weak_topic && <Badge tone="warning">Needs attention</Badge>}
                  </div>
                  <div className="mt-3">
                    <MasteryBar value={tm.mastery_probability} />
                  </div>
                  <p className="mt-2 text-xs text-ink-muted">
                    {tm.correct_count}/{tm.attempts_count} correct
                  </p>
                </Panel>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-display text-2xl">{value}</p>
      <p className="text-xs text-ink-muted">{label}</p>
    </div>
  );
}
