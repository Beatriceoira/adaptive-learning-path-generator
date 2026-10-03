"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import * as api from "./api";
import type { User } from "./types";

const TOKEN_STORAGE_KEY = "lp_token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // If any authenticated request later comes back 401 (token expired --
  // the backend's default lifetime is 60 minutes), drop the session so
  // useRequireAuth redirects to /login.
  useEffect(() => {
    api.setUnauthorizedHandler(() => {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      setToken(null);
      setUser(null);
    });
    return () => api.setUnauthorizedHandler(null);
  }, []);

  // On first load, try to resume a session from a token stashed in a
  // previous visit. If the token's gone stale (expired / revoked), getMe
  // will fail and we just drop back to a logged-out state.
  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_STORAGE_KEY) : null;
    if (!stored) {
      setIsLoading(false);
      return;
    }
    api
      .getMe(stored)
      .then((me) => {
        setToken(stored);
        setUser(me);
      })
      .catch(() => {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      })
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await api.login(email, password);
    const me = await api.getMe(access_token);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
    setToken(access_token);
    setUser(me);
  }

  async function signup(email: string, password: string, fullName?: string) {
    await api.signup(email, password, fullName);
    // Signup doesn't hand back a token (it just creates the account), so log
    // in immediately after -- the learner shouldn't have to retype their
    // credentials right after creating them.
    await login(email, password);
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, token, isLoading, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

/**
 * Redirects to /login once the initial session check has finished and no
 * token was found. Call this at the top of any page that requires auth --
 * it returns the same values as useAuth() so most pages only need this one
 * call. While isLoading is true, render a loading state rather than the
 * protected content, so a not-logged-in visitor never sees a flash of it.
 */
export function useRequireAuth(): AuthContextValue {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!auth.isLoading && !auth.token) {
      router.replace("/login");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.isLoading, auth.token]);

  return auth;
}
