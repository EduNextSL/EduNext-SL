import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { fetchCurrentUser, logout, type User } from "../../api/auth";
import { ApiError, refreshAccessToken, setAccessToken } from "../../api/client";
import { AuthContext, type AuthContextValue, type AuthStatus } from "./authContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("initializing");
  const [user, setUser] = useState<User | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const cancelled = useRef(false);

  // Restore a session from the refresh cookie. Pages stay behind the
  // "initializing" state until this settles, so no protected page renders early.
  useEffect(() => {
    cancelled.current = false;

    function finish(next: AuthStatus, nextUser: User | null) {
      if (cancelled.current) return;
      setUser(nextUser);
      setErrorMessage(null);
      setStatus(next);
    }

    (async () => {
      try {
        const token = await refreshAccessToken();
        if (!token) return finish("unauthenticated", null);
        finish("authenticated", await fetchCurrentUser());
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          setAccessToken(null);
          return finish("unauthenticated", null);
        }
        if (cancelled.current) return;
        setUser(null);
        setErrorMessage(
          error instanceof ApiError ? error.message : "Something went wrong.",
        );
        setStatus("error");
      }
    })();

    return () => {
      cancelled.current = true;
    };
  }, [attempt]);

  const signIn = useCallback((nextUser: User) => {
    setUser(nextUser);
    setErrorMessage(null);
    setStatus("authenticated");
  }, []);

  const signOut = useCallback(async () => {
    try {
      await logout();
    } catch {
      // The local session is dropped even if the server could not be reached.
    }
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const retry = useCallback(() => {
    setStatus("initializing");
    setAttempt((n) => n + 1);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, errorMessage, signIn, signOut, retry }),
    [status, user, errorMessage, signIn, signOut, retry],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
