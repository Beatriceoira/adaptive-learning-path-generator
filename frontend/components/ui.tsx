"use client";

import { ButtonHTMLAttributes, ReactNode, forwardRef } from "react";
import Link from "next/link";
import clsx from "clsx";

type ButtonVariant = "primary" | "secondary" | "ghost";

function buttonClasses(variant: ButtonVariant): string {
  return clsx(
    "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors",
    "disabled:cursor-not-allowed disabled:opacity-50",
    variant === "primary" && "bg-accent text-ink hover:bg-accent-deep",
    variant === "secondary" && "border border-line bg-panel text-ink hover:border-ink",
    variant === "ghost" && "text-ink-muted hover:text-ink"
  );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", className, ...props },
  ref
) {
  return <button ref={ref} className={clsx(buttonClasses(variant), className)} {...props} />;
});

// A link that looks like a button. Use this instead of nesting <Button> inside
// <Link>: a <button> inside an <a> is invalid HTML (nested interactive
// content) and gives keyboard / screen-reader users two tab stops for one action.
export function LinkButton({
  href,
  variant = "primary",
  className,
  children,
}: {
  href: string;
  variant?: ButtonVariant;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={clsx(buttonClasses(variant), className)}>
      {children}
    </Link>
  );
}

export function Panel({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={clsx("rounded-md border border-line bg-panel p-6", className)}>{children}</div>;
}

type BadgeTone = "neutral" | "success" | "warning" | "accent";

// Text colors are chosen to stay above 4.5:1 contrast on their tinted backgrounds
// (badge text is small, so it needs the full WCAG AA ratio).
export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={clsx(
        "inline-block rounded-sm px-2 py-0.5 text-xs font-medium",
        tone === "neutral" && "bg-line/60 text-ink-muted",
        tone === "success" && "bg-sage/15 text-sage-deep",
        tone === "warning" && "bg-rust/15 text-rust",
        tone === "accent" && "bg-accent/25 text-ink"
      )}
    >
      {children}
    </span>
  );
}

export function statusBadgeTone(status: string): BadgeTone {
  if (status === "completed") return "success";
  if (status === "in_progress") return "accent";
  return "neutral";
}

export function statusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

const DIFFICULTY_LABELS: Record<number, string> = {
  1: "Beginner",
  2: "Easy",
  3: "Moderate",
  4: "Challenging",
  5: "Advanced",
};

export function difficultyLabel(level: number): string {
  return DIFFICULTY_LABELS[level] ?? `Level ${level}`;
}

export function MasteryBar({ value }: { value: number }) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  return (
    <div className="flex items-center gap-2">
      <div
        role="progressbar"
        aria-label="Mastery"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="h-2 flex-1 overflow-hidden rounded-full bg-line"
      >
        <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-9 text-right text-xs tabular-nums text-ink-muted">{pct}%</span>
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <p role="status" className="text-sm text-ink-muted">
      {label}
    </p>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-md border border-rust/30 bg-rust/5 px-4 py-3 text-sm text-rust">
      {message}
    </div>
  );
}
