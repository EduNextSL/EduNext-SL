import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { registerCompany, type User } from "../../../api/auth";
import { PasswordField } from "../../../components/PasswordField";
import { TextField } from "../../../components/TextField";
import { firstError, useRegistration } from "./useRegistration";

type CompanyRegisterFormProps = {
  onSwitchToLogin: () => void;
  onAuthenticated: (user: User) => void;
};

export function CompanyRegisterForm({
  onSwitchToLogin,
  onAuthenticated,
}: CompanyRegisterFormProps) {
  const { t } = useTranslation();
  const [companyName, setCompanyName] = useState("");
  const [contactName, setContactName] = useState("");
  const [workEmail, setWorkEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);

  const { busy, fieldErrors, formError, submit } = useRegistration({
    register: () =>
      registerCompany({
        company_name: companyName.trim(),
        contact_full_name: contactName.trim(),
        work_email: workEmail.trim(),
        password,
        password_confirm: passwordConfirm,
        terms_accepted: termsAccepted,
      }),
    email: workEmail.trim(),
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
      <TextField
        name="company_name"
        label={t("common.companyName")}
        value={companyName}
        onChange={setCompanyName}
        autoComplete="organization"
        error={firstError(fieldErrors, "company_name")}
      />
      <TextField
        name="contact_full_name"
        label={t("common.contactName")}
        value={contactName}
        onChange={setContactName}
        autoComplete="name"
        error={firstError(fieldErrors, "contact_full_name")}
      />
      <TextField
        type="email"
        name="work_email"
        label={t("common.workEmail")}
        value={workEmail}
        onChange={setWorkEmail}
        autoComplete="email"
        error={firstError(fieldErrors, "work_email", "email")}
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
        {busy ? t("auth.creating") : t("register.companySubmit")}
      </button>

      <p className="switch-copy">
        {t("common.alreadyHaveAccount")}{" "}
        <button type="button" className="inline-link" onClick={onSwitchToLogin}>
          {t("common.signIn")}
        </button>
      </p>
    </form>
  );
}
