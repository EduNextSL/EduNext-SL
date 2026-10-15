import { FaFacebookF } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";
import { useTranslation } from "react-i18next";

type StudentRegisterFormProps = {
  onSwitchToLogin: () => void;
};

export function StudentRegisterForm({
  onSwitchToLogin,
}: StudentRegisterFormProps) {
  const { t } = useTranslation();

  return (
    <form className="auth-form auth-form--register">
      <div className="two-col-fields">
        <label className="auth-field" aria-label={t("common.firstName")}>
          <input
            type="text"
            placeholder={t("common.firstName")}
            defaultValue=""
          />
        </label>

        <label className="auth-field" aria-label={t("common.lastName")}>
          <input
            type="text"
            placeholder={t("common.lastName")}
            defaultValue=""
          />
        </label>
      </div>

      <label className="auth-field" aria-label={t("common.emailAddress")}>
        <input
          type="email"
          placeholder={t("common.emailAddress")}
          defaultValue=""
        />
      </label>

      <div className="two-col-fields">
        <label
          className="auth-field auth-field--password"
          aria-label={t("common.password")}
        >
          <input
            type="password"
            placeholder={t("common.password")}
            defaultValue=""
          />
          <span className="field-eye" aria-hidden="true">
            ◌
          </span>
        </label>

        <label
          className="auth-field auth-field--password"
          aria-label={t("common.confirmPassword")}
        >
          <input
            type="password"
            placeholder={t("common.confirmPassword")}
            defaultValue=""
          />
          <span className="field-eye" aria-hidden="true">
            ◌
          </span>
        </label>
      </div>

      <p className="helper-copy">{t("common.passwordHelp")}</p>

      <label className="terms-row">
        <input type="checkbox" />
        <span>
          {t("common.termsPrefix")} <a href="#">{t("common.termsOfService")}</a>
          {t("common.termsMiddle")} <a href="#">{t("common.privacyPolicy")}</a>
          {t("common.termsSuffix")}
        </span>
      </label>

      <button type="submit" className="primary-button">
        {t("register.studentSubmit")}
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

      <div className="social-login-row social-login-row--split">
        <button
          type="button"
          className="social-button social-button--google"
          aria-label={t("common.googleSignup")}
        >
          <FcGoogle aria-hidden="true" />
        </button>
        <button
          type="button"
          className="social-button social-button--facebook"
          aria-label={t("common.facebookSignup")}
        >
          <FaFacebookF aria-hidden="true" />
        </button>
      </div>
    </form>
  );
}
