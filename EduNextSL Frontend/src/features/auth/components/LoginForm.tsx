import { FaFacebookF } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";
import { useTranslation } from "react-i18next";

type LoginFormProps = {
  onSwitchToRegister: () => void;
};

export function LoginForm({ onSwitchToRegister }: LoginFormProps) {
  const { t } = useTranslation();

  return (
    <form className="auth-form auth-form--login">
      <label className="auth-field" aria-label={t("common.email")}>
        <input type="email" placeholder={t("common.email")} defaultValue="" />
      </label>

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

      <div className="auth-meta-row">
        <label className="remember-me">
          <input type="checkbox" />
          <span>{t("login.rememberMe")}</span>
        </label>

        <button type="button" className="text-link">
          {t("login.forgotPassword")}
        </button>
      </div>

      <button type="submit" className="primary-button">
        {t("login.submit")}
      </button>

      <div className="auth-divider">
        <span>{t("login.divider")}</span>
      </div>

      <div className="social-login-row">
        <button
          type="button"
          className="social-button social-button--google"
          aria-label={t("login.google")}
        >
          <FcGoogle aria-hidden="true" />
        </button>
        <button
          type="button"
          className="social-button social-button--facebook"
          aria-label={t("login.facebook")}
        >
          <FaFacebookF aria-hidden="true" />
        </button>
      </div>

      <p className="switch-copy">
        {t("login.noAccount")}{" "}
        <button
          type="button"
          className="inline-link"
          onClick={onSwitchToRegister}
        >
          {t("login.signUp")}
        </button>
      </p>
    </form>
  );
}
