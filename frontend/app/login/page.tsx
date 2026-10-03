"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { Button, ErrorState, Panel } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push("/subjects");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong logging in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="text-3xl">Log in</h1>
      <Panel className="mt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm text-ink-muted">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm text-ink-muted">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 text-sm"
            />
          </div>
          {error && <ErrorState message={error} />}
          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? "Logging in…" : "Log in"}
          </Button>
        </form>
      </Panel>
      <p className="mt-4 text-sm text-ink-muted">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-ink underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
