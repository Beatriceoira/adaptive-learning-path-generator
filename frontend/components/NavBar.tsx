"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { APP_NAME } from "@/lib/constants";

export function NavBar() {
  const { user, token, logout } = useAuth();

  return (
    <header className="border-b border-line">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-display text-lg text-ink">
          {APP_NAME}
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          {token ? (
            <>
              <Link href="/subjects" className="text-ink-muted hover:text-ink">
                Subjects
              </Link>
              <span className="hidden max-w-[12rem] truncate text-ink-muted sm:inline">{user?.full_name || user?.email}</span>
              <button onClick={logout} className="text-ink-muted hover:text-ink">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-ink-muted hover:text-ink">
                Log in
              </Link>
              <Link href="/signup" className="text-ink">
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
