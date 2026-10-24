import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { requestPasswordReset } from "../../../api/auth";
import { ApiError } from "../../../api/client";
import { TextField } from "../../../components/TextField";
import { AuthLayout } from "../components/AuthLayout";

export function ForgotPasswordPage({ onBackToLogin }: { onBackToLogin: () => void }) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setError(null);
    if (!email.trim()) {
      setError(t("auth.enterEmail"));
      return;
    }
    setBusy(true);
    try {
      await requestPasswordReset(email.trim());
      setSent(true); // same message whether or not the account exists
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.genericError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-app-shell">
      <AuthLayout
        title={t("auth.forgotTitle")}
        subtitle={t("auth.forgotSubtitle")}
        form={
          sent ? (
            <div className="auth-form" role="status">
              <p>{t("auth.resetSent")}</p>
              <button type="button" className="primary-button" onClick={onBackToLogin}>
                {t("auth.backToLogin")}
              </button>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              <TextField
                type="email"
                name="email"
                label={t("common.email")}
                value={email}
                onChange={setEmail}
                autoComplete="email"
              />
              {error && (
                <p className="form-error" role="alert">
                  {error}
                </p>
              )}
              <button type="submit" className="primary-button" disabled={busy}>
                {busy ? t("auth.sending") : t("auth.sendLink")}
              </button>
              <p className="switch-copy">
                <button type="button" className="inline-link" onClick={onBackToLogin}>
                  {t("auth.backToLogin")}
                </button>
              </p>
            </form>
          )
        }
      />
    </main>
  );
}
