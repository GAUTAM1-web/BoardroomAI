"use client";

import { LogOut, ShieldCheck, Sparkles, UserRound, Users } from "lucide-react";
import { type FormEvent, type ReactNode, useCallback, useEffect, useState } from "react";

import {
  createAuthSession,
  fetchAuthConfig,
  fetchAuthSession,
  logoutAuthSession
} from "@/lib/api";
import type { AuthConfig, AuthMode, AuthSession } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const SESSION_STORAGE_KEY = "boardroom.authSession";

const fallbackAuthConfig: AuthConfig = {
  email_login: true,
  demo_account: true,
  guest_mode: true,
  session_persistence: true,
  oauth_ready: [{ provider: "google", enabled: false }]
};

export function AuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [config, setConfig] = useState<AuthConfig>(fallbackAuthConfig);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const persistSession = useCallback((nextSession: AuthSession) => {
    setSession(nextSession);
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
  }, []);

  const signIn = useCallback(
    async (mode: AuthMode, userEmail?: string) => {
      setBusy(true);
      try {
        const nextSession = await createAuthSession({ mode, email: userEmail });
        persistSession(nextSession);
        setError(null);
      } catch (authError) {
        if (mode === "demo" || mode === "guest") {
          persistSession(localSession(mode, userEmail));
          setError(null);
        } else {
          setError(authError instanceof Error ? authError.message : "Login failed");
        }
      } finally {
        setBusy(false);
      }
    },
    [persistSession]
  );

  useEffect(() => {
    const stored = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as AuthSession;
        if (new Date(parsed.expires_at).getTime() > Date.now()) {
          setSession(parsed);
        }
      } catch {
        window.localStorage.removeItem(SESSION_STORAGE_KEY);
      }
    }

    void fetchAuthConfig().then(setConfig).catch(() => setConfig(fallbackAuthConfig));
    void fetchAuthSession()
      .then((status) => {
        if (status.authenticated && status.session) {
          persistSession(status.session);
        }
      })
      .catch(() => undefined);
  }, [persistSession]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("auth") === "demo" && !session && !busy) {
      void signIn("demo");
    }
  }, [busy, session, signIn]);

  async function handleEmailLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim()) {
      setError("Enter an email address to continue.");
      return;
    }
    await signIn("email", email.trim());
  }

  async function logout() {
    setBusy(true);
    try {
      await logoutAuthSession();
    } catch {
      // Local cleanup still completes secure logout from the browser's perspective.
    } finally {
      window.localStorage.removeItem(SESSION_STORAGE_KEY);
      setSession(null);
      setBusy(false);
    }
  }

  if (!session) {
    return (
      <main className="min-h-screen bg-board-ink px-4 py-6 text-board-mist">
        <section className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-6xl place-items-center">
          <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,1fr)_420px]">
            <div className="flex min-w-0 flex-col justify-center">
              <div className="mb-4 flex items-center gap-2 text-board-teal">
                <ShieldCheck className="h-5 w-5" />
                <span className="text-sm font-medium">Secure workspace access</span>
              </div>
              <h1 className="max-w-3xl break-words text-4xl font-semibold text-white md:text-6xl">
                Enter the BoardroomAI operating workspace.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-board-muted">
                Use a demo account for portfolio walkthroughs, guest mode for read-only review, or
                email login for team workspaces. Sessions persist locally and can be cleared with
                secure logout.
              </p>
            </div>

            <div className="glass-panel rounded-lg p-4">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-white">Sign in</h2>
                <p className="mt-1 text-sm text-board-muted">
                  Google OAuth is prepared in the backend config and can be enabled with provider
                  credentials.
                </p>
              </div>
              <div className="grid gap-2">
                <Button
                  type="button"
                  onClick={() => void signIn("demo")}
                  disabled={busy || !config.demo_account}
                >
                  <Sparkles className="h-4 w-4" />
                  Launch demo account
                </Button>
                <Button
                  type="button"
                  variant="quiet"
                  onClick={() => void signIn("guest")}
                  disabled={busy || !config.guest_mode}
                >
                  <Users className="h-4 w-4" />
                  Continue as guest
                </Button>
              </div>
              <form className="mt-4 border-t border-white/10 pt-4" onSubmit={handleEmailLogin}>
                <label className="block">
                  <span className="mb-2 block text-xs font-medium text-board-muted">
                    Email address
                  </span>
                  <Input
                    value={email}
                    type="email"
                    placeholder="founder@company.com"
                    onChange={(event) => setEmail(event.target.value)}
                    disabled={!config.email_login}
                  />
                </label>
                <Button type="submit" variant="quiet" className="mt-3 w-full" disabled={busy}>
                  <UserRound className="h-4 w-4" />
                  Continue with email
                </Button>
              </form>
              {error ? (
                <div className="mt-3 rounded-md border border-board-rose/30 bg-board-rose/10 p-3 text-sm text-board-rose">
                  {error}
                </div>
              ) : null}
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-board-ink">
      <div className="border-b border-white/10 bg-board-panel/90 px-4 py-2 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 text-sm text-board-muted">
            <span className="text-board-mist">{session.user.display_name}</span>
            <span className="mx-2 text-white/20">/</span>
            <span>{session.user.role}</span>
            <span className="mx-2 text-white/20">/</span>
            <span>{session.user.organization}</span>
          </div>
          <Button type="button" variant="quiet" size="sm" onClick={() => void logout()} disabled={busy}>
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>
      <div className={cn("min-h-0")}>{children}</div>
    </div>
  );
}

function localSession(mode: AuthMode, email?: string): AuthSession {
  const now = new Date();
  const expires = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  const demo = mode === "demo";
  return {
    authenticated: true,
    session_id: `local-${mode}-${now.getTime()}`,
    mode,
    user: {
      email: email || (demo ? "demo@boardroom.local" : "guest@boardroom.local"),
      display_name: demo ? "Demo Executive" : "Guest Reviewer",
      role: demo ? "Administrator" : "Viewer",
      organization: "Default Organization"
    },
    issued_at: now.toISOString(),
    expires_at: expires.toISOString()
  };
}
