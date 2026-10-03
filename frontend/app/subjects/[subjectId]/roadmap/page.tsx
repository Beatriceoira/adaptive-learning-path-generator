"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, generateRoadmap, getActiveRoadmap } from "@/lib/api";
import type { Roadmap } from "@/lib/types";
import {
  Badge,
  Button,
  ErrorState,
  LinkButton,
  LoadingState,
  Panel,
  statusBadgeTone,
  statusLabel,
} from "@/components/ui";

export default function RoadmapPage({ params }: { params: { subjectId: string } }) {
  const { subjectId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();

  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [hasChecked, setHasChecked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getActiveRoadmap(token, subjectId)
      .then((r) => {
        if (cancelled) return;
        setRoadmap(r);
        setHasChecked(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Couldn't load your roadmap.");
        setHasChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, [token, subjectId]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  async function handleGenerate() {
    if (!token) return;
    setError(null);
    setIsGenerating(true);
    try {
      const r = await generateRoadmap(token, subjectId);
      setRoadmap(r);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate a roadmap.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl">Roadmap</h1>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}
      {!hasChecked && !error && (
        <div className="mt-6">
          <LoadingState label="Loading your roadmap…" />
        </div>
      )}

      {hasChecked && !roadmap && (
        <Panel className="mt-6">
          <p className="text-ink-muted">
            No roadmap yet. Generating one orders every topic in this subject by prerequisite, and marks anything
            you&apos;ve already tested well on as done.
          </p>
          <Button className="mt-5" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? "Generating…" : "Generate my roadmap"}
          </Button>
        </Panel>
      )}

      {roadmap && (
        <div className="mt-6">
          {roadmap.rationale && (
            <Panel>
              <p className="text-ink-muted">{roadmap.rationale}</p>
            </Panel>
          )}

          <ol className="mt-6">
            {roadmap.steps.map((step) => (
              <li key={step.topic_id} className="flex items-center justify-between gap-4 border-b border-line py-3">
                <div className="flex items-center gap-4">
                  <span className="w-6 font-display text-lg text-ink-muted">{step.sequence_order + 1}</span>
                  <span>{step.topic_name}</span>
                  <Badge tone={statusBadgeTone(step.status)}>{statusLabel(step.status)}</Badge>
                </div>
                <div className="flex shrink-0 gap-3">
                  <LinkButton href={`/topics/${step.topic_id}/study`} variant="secondary">
                    Study
                  </LinkButton>
                  <LinkButton href={`/topics/${step.topic_id}/quiz`} variant="secondary">
                    Practice
                  </LinkButton>
                </div>
              </li>
            ))}
          </ol>

          <Button variant="ghost" className="mt-6" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? "Regenerating…" : "Regenerate roadmap"}
          </Button>
        </div>
      )}
    </div>
  );
}
