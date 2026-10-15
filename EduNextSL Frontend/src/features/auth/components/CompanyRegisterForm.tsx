import { useTranslation } from "react-i18next";

type CompanyRegisterFormProps = {
  onSwitchToLogin: () => void;
};

export function CompanyRegisterForm({
  onSwitchToLogin,
}: CompanyRegisterFormProps) {
  const { t } = useTranslation();

  return (
    <form className="auth-form auth-form--register">
      <label className="auth-field" aria-label={t("common.companyName")}>
        <input
          type="text"
          placeholder={t("common.companyName")}
          defaultValue=""
        />
      </label>

      <label className="auth-field" aria-label={t("common.contactName")}>
        <input
          type="text"
          placeholder={t("common.contactName")}
          defaultValue=""
        />
      </label>

      <label className="auth-field" aria-label={t("common.workEmail")}>
        <input
          type="email"
          placeholder={t("common.workEmail")}
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
        {t("register.companySubmit")}
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
