"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { LinkButton } from "@/components/ui";

const STEPS = [
  {
    title: "Take a diagnostic",
    body: "A short quiz on the fundamentals places you at your real starting point, so you never have to guess your own level.",
  },
  {
    title: "Get your roadmap",
    body: "Topics are ordered by what actually depends on what, so you never hit something before its prerequisites.",
  },
  {
    title: "Practice at your level",
    body: "Every question's difficulty adjusts to your current mastery, one answer at a time.",
  },
  {
    title: "See what needs attention",
    body: "Topics you keep missing get flagged, with a clear next step back on track.",
  },
];

export default function HomePage() {
  const { token, isLoading } = useAuth();

  // Logged-in learners get a short welcome instead of the pitch. Everyone else,
  // including visitors while the session check is still running, sees the hero,
  // so the page's real content is in the server-rendered HTML rather than a spinner.
  if (!isLoading && token) {
    return (
      <div className="max-w-xl">
        <h1 className="text-3xl">Welcome back</h1>
        <p className="mt-3 text-ink-muted">Pick up where you left off, or explore a new subject.</p>
        <LinkButton href="/subjects" className="mt-6">
          Go to your subjects
        </LinkButton>
      </div>
    );
  }

  return (
    <div>
      <section className="max-w-2xl">
        <h1 className="text-4xl leading-tight sm:text-5xl">Start where you actually are.</h1>
        <p className="mt-5 text-lg text-ink-muted">
          An AI tutor that works out what you already know, builds a roadmap around real prerequisites, and adjusts
          every practice question to how you&apos;re doing.
        </p>
        <div className="mt-8 flex items-center gap-5">
          <LinkButton href="/signup">Create your account</LinkButton>
          <Link href="/login" className="text-sm text-ink-muted hover:text-ink">
            Log in
          </Link>
        </div>
      </section>

      <section className="mt-20 max-w-3xl border-t border-line pt-10">
        <ol className="space-y-8">
          {STEPS.map((step, i) => (
            <li key={step.title} className="flex gap-5">
              <span className="font-display text-2xl text-accent-deep">{i + 1}</span>
              <div>
                <h3 className="text-lg">{step.title}</h3>
                <p className="mt-1 text-ink-muted">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
