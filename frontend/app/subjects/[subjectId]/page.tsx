"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/auth-context";
import { ApiError, getSubjects, getTopicsForSubject } from "@/lib/api";
import type { Subject, Topic } from "@/lib/types";
import { ErrorState, LinkButton, LoadingState, Panel } from "@/components/ui";

export default function SubjectHubPage({ params }: { params: { subjectId: string } }) {
  const { subjectId } = params;
  const { token, isLoading: authLoading } = useRequireAuth();
  const [subject, setSubject] = useState<Subject | null>(null);
  const [topics, setTopics] = useState<Topic[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    // There's no single-subject endpoint, so find this subject in the list.
    Promise.all([getSubjects(), getTopicsForSubject(subjectId)])
      .then(([subjects, topicsList]) => {
        if (cancelled) return;
        setSubject(subjects.find((s) => s.id === subjectId) ?? null);
        setTopics(topicsList);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't load this subject.");
      });
    return () => {
      cancelled = true;
    };
  }, [token, subjectId]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null;

  return (
    <div>
      <h1 className="text-3xl">{subject?.name ?? "Subject"}</h1>
      {subject?.description && <p className="mt-2 text-ink-muted">{subject.description}</p>}
      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link href={`/subjects/${subjectId}/assessment`} className="block">
          <Panel className="h-full transition-colors hover:border-ink">
            <h3 className="text-lg">Diagnostic</h3>
            <p className="mt-1 text-sm text-ink-muted">Find your starting point with a short quiz.</p>
          </Panel>
        </Link>
        <Link href={`/subjects/${subjectId}/roadmap`} className="block">
          <Panel className="h-full transition-colors hover:border-ink">
            <h3 className="text-lg">Roadmap</h3>
            <p className="mt-1 text-sm text-ink-muted">See your personalized topic order.</p>
          </Panel>
        </Link>
        <Link href={`/subjects/${subjectId}/recommendations`} className="block">
          <Panel className="h-full transition-colors hover:border-ink">
            <h3 className="text-lg">Recommendations</h3>
            <p className="mt-1 text-sm text-ink-muted">What to focus on right now.</p>
          </Panel>
        </Link>
        <Link href={`/subjects/${subjectId}/progress`} className="block">
          <Panel className="h-full transition-colors hover:border-ink">
            <h3 className="text-lg">Progress</h3>
            <p className="mt-1 text-sm text-ink-muted">Mastery, accuracy, and activity over time.</p>
          </Panel>
        </Link>
      </div>

      <h2 className="mt-12 text-xl">Topics</h2>
      <div className="mt-4">
        {!error && topics === null && <LoadingState label="Loading topics…" />}
        {topics !== null && topics.length === 0 && (
          <p className="text-sm text-ink-muted">This subject doesn&apos;t have any topics yet.</p>
        )}
        {topics?.map((topic) => (
          <div key={topic.id} className="flex items-center justify-between gap-4 border-b border-line py-3">
            <div>
              <p>{topic.name}</p>
              {topic.description && <p className="text-sm text-ink-muted">{topic.description}</p>}
            </div>
            <div className="flex shrink-0 gap-3">
              <LinkButton href={`/topics/${topic.id}/study`} variant="secondary">
                Study
              </LinkButton>
              <LinkButton href={`/topics/${topic.id}/quiz`} variant="secondary">
                Practice
              </LinkButton>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
