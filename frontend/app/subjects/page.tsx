"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/auth-context";
import { getSubjects, ApiError } from "@/lib/api";
import type { Subject } from "@/lib/types";
import { ErrorState, LoadingState, Panel } from "@/components/ui";

export default function SubjectsPage() {
  const { token, isLoading: authLoading } = useRequireAuth();
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getSubjects()
      .then((list) => {
        if (!cancelled) setSubjects(list);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Couldn't load subjects.");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (authLoading) return <LoadingState label="Checking your session…" />;
  if (!token) return null; // useRequireAuth is redirecting to /login

  return (
    <div>
      <h1 className="text-3xl">Subjects</h1>
      <p className="mt-2 text-ink-muted">Pick a subject to start your diagnostic, roadmap, or practice.</p>

      <div className="mt-8 space-y-3">
        {error && <ErrorState message={error} />}
        {!error && subjects === null && <LoadingState label="Loading subjects…" />}
        {subjects !== null && subjects.length === 0 && (
          <p className="text-sm text-ink-muted">
            No subjects exist yet. Seed one with <code>python -m scripts.seed</code> in the backend, or create one
            through <code>POST /api/subjects</code>.
          </p>
        )}
        {subjects?.map((subject) => (
          <Link key={subject.id} href={`/subjects/${subject.id}`} className="block">
            <Panel className="transition-colors hover:border-ink">
              <h3 className="text-lg">{subject.name}</h3>
              {subject.description && <p className="mt-1 text-sm text-ink-muted">{subject.description}</p>}
            </Panel>
          </Link>
        ))}
      </div>
    </div>
  );
}
