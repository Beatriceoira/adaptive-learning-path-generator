"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, getRecommendations } from "@/lib/api";
import type { Recommendations } from "@/lib/types";
import { Badge, ErrorState, LinkButton, LoadingState, MasteryBar, Panel, difficultyLabel } from "@/components/ui";

export default function RecommendationsPage({ params }: { params: { subjectId: string } }) {
  const { subjectId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();

  const [data, setData] = useState<Recommendations | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getRecommendations(token, subjectId)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't load recommendations.");
      });
    return () => {
      cancelled = true;
    };
  }, [token, subjectId]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl">Recommendations</h1>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}
      {!data && !error && (
        <div className="mt-6">
          <LoadingState label="Loading…" />
        </div>
      )}

      {data && (
        <div className="mt-6 space-y-8">
          <Panel>
            <p className="text-ink-muted">{data.message}</p>
          </Panel>

          {data.weak_topics.length > 0 && (
            <section>
              <h2 className="text-xl">Needs attention</h2>
              <div className="mt-4 space-y-3">
                {data.weak_topics.map((wt) => (
                  <Panel key={wt.topic_id}>
                    <div className="flex items-center justify-between gap-3">
                      <h3>{wt.topic_name}</h3>
                      <Badge tone="warning">Practice at {difficultyLabel(wt.recommended_difficulty)}</Badge>
                    </div>
                    <div className="mt-3">
                      <MasteryBar value={wt.mastery_probability} />
                    </div>
                    <div className="mt-4 flex gap-3">
                      <LinkButton href={`/topics/${wt.topic_id}/study`} variant="secondary">
                        Review material
                      </LinkButton>
                      <LinkButton href={`/topics/${wt.topic_id}/quiz`} variant="secondary">
                        Practice now
                      </LinkButton>
                    </div>
                  </Panel>
                ))}
              </div>
            </section>
          )}

          {data.next_up.length > 0 && (
            <section>
              <h2 className="text-xl">Next up in your roadmap</h2>
              <div className="mt-4 space-y-3">
                {data.next_up.map((nu) => (
                  <Panel key={nu.topic_id} className="flex items-center justify-between gap-3">
                    <span>{nu.topic_name}</span>
                    <div className="flex gap-3">
                      <LinkButton href={`/topics/${nu.topic_id}/study`} variant="secondary">
                        Study
                      </LinkButton>
                      <LinkButton href={`/topics/${nu.topic_id}/quiz`} variant="secondary">
                        Practice
                      </LinkButton>
                    </div>
                  </Panel>
                ))}
              </div>
            </section>
          )}

          {data.weak_topics.length === 0 && data.next_up.length === 0 && (
            <LinkButton href={`/subjects/${subjectId}/roadmap`}>View or generate your roadmap</LinkButton>
          )}
        </div>
      )}
    </div>
  );
}
