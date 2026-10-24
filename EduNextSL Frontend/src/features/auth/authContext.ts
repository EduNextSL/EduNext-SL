import { createContext, useContext } from "react";
import type { User } from "../../api/auth";

export type AuthStatus =
  | "initializing"
  | "authenticated"
  | "unauthenticated"
  | "error";

export type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  /** Set when status is "error" (server unreachable while restoring the session). */
  errorMessage: string | null;
  signIn: (user: User) => void;
  signOut: () => Promise<void>;
  retry: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}
