import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { registerStudent, type User } from "../../../api/auth";
import { PasswordField } from "../../../components/PasswordField";
import { TextField } from "../../../components/TextField";
import { SocialButtons } from "./SocialButtons";
import { firstError, useRegistration } from "./useRegistration";

type StudentRegisterFormProps = {
  onSwitchToLogin: () => void;
  onAuthenticated: (user: User) => void;
};

export function StudentRegisterForm({
  onSwitchToLogin,
  onAuthenticated,
}: StudentRegisterFormProps) {
  const { t } = useTranslation();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);

  const { busy, fieldErrors, formError, submit } = useRegistration({
    register: () =>
      registerStudent({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
        password_confirm: passwordConfirm,
        terms_accepted: termsAccepted,
      }),
    email: email.trim(),
    password,
    onAuthenticated,
    onSwitchToLogin,
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void submit();
  }

  return (
    <form className="auth-form auth-form--register" onSubmit={handleSubmit} noValidate>
      <div className="two-col-fields">
        <TextField
          name="first_name"
          label={t("common.firstName")}
          value={firstName}
          onChange={setFirstName}
          autoComplete="given-name"
          error={firstError(fieldErrors, "first_name")}
        />
        <TextField
          name="last_name"
          label={t("common.lastName")}
          value={lastName}
          onChange={setLastName}
          autoComplete="family-name"
          error={firstError(fieldErrors, "last_name")}
        />
      </div>

      <TextField
        type="email"
        name="email"
        label={t("common.emailAddress")}
        value={email}
        onChange={setEmail}
        autoComplete="email"
        error={firstError(fieldErrors, "email")}
      />

      <div className="two-col-fields">
        <PasswordField
          name="password"
          label={t("common.password")}
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          error={firstError(fieldErrors, "password")}
        />
        <PasswordField
          name="password_confirm"
          label={t("common.confirmPassword")}
          value={passwordConfirm}
          onChange={setPasswordConfirm}
          autoComplete="new-password"
          error={firstError(fieldErrors, "password_confirm")}
        />
      </div>

      <p className="helper-copy">{t("common.passwordHelp")}</p>

      <label className="terms-row">
        <input
          type="checkbox"
          checked={termsAccepted}
          onChange={(event) => setTermsAccepted(event.target.checked)}
        />
        <span>
          {t("common.termsPrefix")} <a href="#">{t("common.termsOfService")}</a>
          {t("common.termsMiddle")} <a href="#">{t("common.privacyPolicy")}</a>
          {t("common.termsSuffix")}
        </span>
      </label>
      {firstError(fieldErrors, "terms_accepted") && (
        <p className="field-error" role="alert">
          {firstError(fieldErrors, "terms_accepted")}
        </p>
      )}

      {formError && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}

      <button type="submit" className="primary-button" disabled={busy}>
        {busy ? t("auth.creating") : t("register.studentSubmit")}
      </button>

      <p className="switch-copy">
        {t("common.alreadyHaveAccount")}{" "}
        <button type="button" className="inline-link" onClick={onSwitchToLogin}>
          {t("common.signIn")}
        </button>
      </p>

      <div className="auth-divider">
        <span>{t("register.divider")}</span>
      </div>

      <SocialButtons split termsAccepted={termsAccepted} onSignedIn={onAuthenticated} />
    </form>
  );
}
