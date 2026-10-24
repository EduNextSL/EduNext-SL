import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { confirmPasswordReset } from "../../../api/auth";
import { ApiError } from "../../../api/client";
import { PasswordField } from "../../../components/PasswordField";
import { AuthLayout } from "../components/AuthLayout";
import { firstError } from "../components/useRegistration";

export function ResetPasswordPage({ onBackToLogin }: { onBackToLogin: () => void }) {
  const { t } = useTranslation();
  const params = new URLSearchParams(window.location.search);
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setErrors({});
    setFormError(null);
    setBusy(true);
    try {
      await confirmPasswordReset(uid, token, password, confirm);
      setDone(true);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fieldErrors).length > 0) {
        setErrors(err.fieldErrors);
      } else {
        setFormError(err instanceof ApiError ? err.message : t("auth.genericError"));
      }
    } finally {
      setBusy(false);
    }
  }

  const linkProblem = !uid || !token || errors.token;

  return (
    <main className="auth-app-shell">
      <AuthLayout
        title={t("auth.resetTitle")}
        subtitle={t("auth.resetSubtitle")}
        form={
          done ? (
            <div className="auth-form" role="status">
              <p>{t("auth.resetDone")}</p>
              <button type="button" className="primary-button" onClick={onBackToLogin}>
                {t("login.submit")}
              </button>
            </div>
          ) : linkProblem ? (
            <div className="auth-form" role="alert">
              <p className="form-error">{firstError(errors, "token") ?? t("auth.resetLinkInvalid")}</p>
              <button type="button" className="primary-button" onClick={onBackToLogin}>
                {t("auth.backToLogin")}
              </button>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              <PasswordField
                name="new_password"
                label={t("auth.newPassword")}
                value={password}
                onChange={setPassword}
                autoComplete="new-password"
                error={firstError(errors, "new_password")}
              />
              <PasswordField
                name="new_password_confirm"
                label={t("common.confirmPassword")}
                value={confirm}
                onChange={setConfirm}
                autoComplete="new-password"
                error={firstError(errors, "new_password_confirm")}
              />
              <p className="helper-copy">{t("common.passwordHelp")}</p>
              {formError && (
                <p className="form-error" role="alert">
                  {formError}
                </p>
              )}
              <button type="submit" className="primary-button" disabled={busy}>
                {busy ? t("auth.saving") : t("auth.resetSubmit")}
              </button>
            </form>
          )
        }
      />
    </main>
  );
}
