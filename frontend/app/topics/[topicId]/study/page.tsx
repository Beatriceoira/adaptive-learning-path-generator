"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import clsx from "clsx";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, generateStudyMaterial, getCachedStudyMaterial, getTopic } from "@/lib/api";
import type { StudyMaterial, Topic } from "@/lib/types";
import { Button, ErrorState, LoadingState, Panel, difficultyLabel } from "@/components/ui";

const LEVELS = [1, 2, 3, 4, 5];

export default function StudyMaterialPage({ params }: { params: { topicId: string } }) {
  const { topicId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();

  const [topic, setTopic] = useState<Topic | null>(null);
  const [difficulty, setDifficulty] = useState(1);
  const [material, setMaterial] = useState<StudyMaterial | null>(null);
  const [hasChecked, setHasChecked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getTopic(topicId)
      .then((t) => {
        if (!cancelled) setTopic(t);
      })
      .catch(() => undefined); // non-fatal: the header just falls back to a generic title
    return () => {
      cancelled = true;
    };
  }, [token, topicId]);

  // Check for cached material whenever the selected level changes. The
  // `cancelled` flag matters here: if the learner clicks through levels
  // quickly, an older request can resolve after a newer one, and without it
  // that stale response would overwrite the current level's state.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setMaterial(null);
    setHasChecked(false);
    setError(null);
    getCachedStudyMaterial(token, topicId, difficulty)
      .then((m) => {
        if (cancelled) return;
        setMaterial(m);
        setHasChecked(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Couldn't check for study material.");
        setHasChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, [token, topicId, difficulty]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  async function handleGenerate(forceRegenerate: boolean) {
    if (!token) return;
    setError(null);
    setIsGenerating(true);
    try {
      const m = await generateStudyMaterial(token, topicId, difficulty, forceRegenerate);
      setMaterial(m);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate study material.");
    } finally {
      setIsGenerating(false);
    }
  }

  // A generation request can finish after the learner has moved to another
  // level. Only show material that actually belongs to the selected level.
  const visibleMaterial = material && material.difficulty_level === difficulty ? material : null;

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl">{topic?.name ?? "Study material"}</h1>
      {topic?.description && <p className="mt-2 text-ink-muted">{topic.description}</p>}

      <div className="mt-6 flex flex-wrap gap-2" role="group" aria-label="Difficulty level">
        {LEVELS.map((level) => (
          <button
            key={level}
            type="button"
            aria-pressed={level === difficulty}
            onClick={() => setDifficulty(level)}
            className={clsx(
              "rounded-md border px-3 py-1.5 text-sm",
              level === difficulty ? "border-ink bg-ink text-paper" : "border-line bg-panel text-ink-muted"
            )}
          >
            {difficultyLabel(level)}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}
      {!hasChecked && !error && (
        <div className="mt-6">
          <LoadingState label="Checking for existing material…" />
        </div>
      )}

      {hasChecked && !visibleMaterial && (
        <Panel className="mt-6">
          <p className="text-ink-muted">No study material generated yet at this level.</p>
          <Button className="mt-4" onClick={() => handleGenerate(false)} disabled={isGenerating}>
            {isGenerating ? "Generating…" : "Generate study material"}
          </Button>
        </Panel>
      )}

      {visibleMaterial && (
        <div className="mt-6">
          <Panel>
            <div className="prose prose-headings:font-display prose-a:text-ink prose-code:text-ink max-w-none">
              <ReactMarkdown>{visibleMaterial.content_markdown}</ReactMarkdown>
            </div>
          </Panel>
          <Button variant="ghost" className="mt-4" onClick={() => handleGenerate(true)} disabled={isGenerating}>
            {isGenerating ? "Regenerating…" : "Regenerate"}
          </Button>
        </div>
      )}
    </div>
  );
}
