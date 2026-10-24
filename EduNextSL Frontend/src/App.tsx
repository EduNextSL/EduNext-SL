import { useCallback, useEffect, useState } from "react";
import "./App.css";
import type { User } from "./api/auth";
import { ErrorScreen, LoadingScreen } from "./components/StatusScreen";
import { useAuth } from "./features/auth/authContext";
import { ForgotPasswordPage } from "./features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "./features/auth/pages/LoginPage";
import { RegisterPage } from "./features/auth/pages/RegisterPage";
import { ResetPasswordPage } from "./features/auth/pages/ResetPasswordPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { usePath } from "./router";

// Signed-in users are sent away from these.
const GUEST_ONLY_PATHS = ["/login", "/register"];
// Reachable whether or not you are signed in (e.g. opened from an email link).
const OPEN_PATHS = ["/forgot-password", "/reset-password"];

function App() {
  const { status, errorMessage, signIn, retry } = useAuth();
  const { path, navigate } = usePath();
  const [accountType, setAccountType] = useState<"student" | "company">("student");

  const authenticated = status === "authenticated";
  const guestOnly = GUEST_ONLY_PATHS.includes(path);
  const open = OPEN_PATHS.includes(path);
  const known = guestOnly || open || path === "/dashboard";

  // Redirects run only once auth state is known, so there are no flashes or loops:
  // signed-in users never see /login, signed-out users never see /dashboard.
  useEffect(() => {
    if (status === "initializing" || status === "error" || open) return;
    if (authenticated && (!known || guestOnly)) {
      navigate("/dashboard", { replace: true });
    } else if (!authenticated && !guestOnly) {
      navigate("/login", { replace: true });
    }
  }, [status, authenticated, known, guestOnly, open, navigate]);

  const handleAuthenticated = useCallback(
    (user: User) => {
      signIn(user);
      navigate("/dashboard", { replace: true });
    },
    [signIn, navigate],
  );
  const toLogin = useCallback(() => navigate("/login"), [navigate]);
  const toRegister = useCallback(() => navigate("/register"), [navigate]);
  const toForgot = useCallback(() => navigate("/forgot-password"), [navigate]);

  if (status === "initializing") return <LoadingScreen />;
  if (status === "error") {
    return <ErrorScreen message={errorMessage ?? ""} onRetry={retry} />;
  }

  if (path === "/forgot-password") return <ForgotPasswordPage onBackToLogin={toLogin} />;
  if (path === "/reset-password") return <ResetPasswordPage onBackToLogin={toLogin} />;

  if (authenticated && path === "/dashboard") return <DashboardPage />;

  if (!authenticated && path === "/login") {
    return (
      <main className="auth-app-shell">
        <LoginPage
          onSwitchToRegister={toRegister}
          onForgotPassword={toForgot}
          onAuthenticated={handleAuthenticated}
        />
      </main>
    );
  }
  if (!authenticated && path === "/register") {
    return (
      <main className="auth-app-shell">
        <RegisterPage
          initialAccountType={accountType}
          onAccountTypeChange={setAccountType}
          onSwitchToLogin={toLogin}
          onAuthenticated={handleAuthenticated}
        />
      </main>
    );
  }

  // A redirect is about to run; never render an empty screen meanwhile.
  return <LoadingScreen />;
}

export default App;
