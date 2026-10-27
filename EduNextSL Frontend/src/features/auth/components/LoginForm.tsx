import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { login, type User } from "../../../api/auth";
import { ApiError } from "../../../api/client";
import { PasswordField } from "../../../components/PasswordField";
import { TextField } from "../../../components/TextField";
import { SocialButtons } from "./SocialButtons";

type LoginFormProps = {
  onSwitchToRegister: () => void;
  onForgotPassword: () => void;
  onAuthenticated: (user: User) => void;
};

export function LoginForm({
  onSwitchToRegister,
  onForgotPassword,
  onAuthenticated,
}: LoginFormProps) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return; // ignore double submits
    setError(null);
    if (!email.trim() || !password) {
      setError(t("auth.enterEmailPassword"));
      return;
    }
    setBusy(true);
    try {
      onAuthenticated(await login(email.trim(), password, rememberMe));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.genericError"));
      setBusy(false);
    }
  }

  return (
    <form className="auth-form auth-form--login" onSubmit={handleSubmit} noValidate>
      <TextField
        type="email"
        name="email"
        label={t("common.email")}
        value={email}
        onChange={setEmail}
        autoComplete="email"
      />
      <PasswordField
        name="password"
        label={t("common.password")}
        value={password}
        onChange={setPassword}
        autoComplete="current-password"
      />

      <div className="auth-meta-row">
        <label className="remember-me">
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={(event) => setRememberMe(event.target.checked)}
          />
          <span>{t("login.rememberMe")}</span>
        </label>

        <button type="button" className="text-link" onClick={onForgotPassword}>
          {t("login.forgotPassword")}
        </button>
      </div>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="primary-button" disabled={busy}>
        {busy ? t("auth.signingIn") : t("login.submit")}
      </button>

      <div className="auth-divider">
        <span>{t("login.divider")}</span>
      </div>

      <SocialButtons rememberMe={rememberMe} onSignedIn={onAuthenticated} />

      <p className="switch-copy">
        {t("login.noAccount")}{" "}
        <button type="button" className="inline-link" onClick={onSwitchToRegister}>
          {t("login.signUp")}
        </button>
      </p>
    </form>
  );
}
