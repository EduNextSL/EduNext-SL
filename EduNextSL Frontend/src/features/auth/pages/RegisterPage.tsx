import { useMemo, useState } from "react";
import { AuthLayout } from "../components/AuthLayout";
import { CompanyRegisterForm } from "../components/CompanyRegisterForm";
import { StudentRegisterForm } from "../components/StudentRegisterForm";
import { useTranslation } from "react-i18next";
import type { User } from "../../../api/auth";

type RegisterPageProps = {
  initialAccountType?: "student" | "company";
  onAccountTypeChange?: (type: "student" | "company") => void;
  onSwitchToLogin: () => void;
  onAuthenticated: (user: User) => void;
};

export function RegisterPage({
  initialAccountType = "student",
  onAccountTypeChange,
  onSwitchToLogin,
  onAuthenticated,
}: RegisterPageProps) {
  const { t } = useTranslation();
  const [accountType, setAccountType] = useState<"student" | "company">(
    initialAccountType,
  );

  const form = useMemo(() => {
    if (accountType === "company") {
      return (
        <CompanyRegisterForm
          onSwitchToLogin={onSwitchToLogin}
          onAuthenticated={onAuthenticated}
        />
      );
    }

    return (
      <StudentRegisterForm
        onSwitchToLogin={onSwitchToLogin}
        onAuthenticated={onAuthenticated}
      />
    );
  }, [accountType, onSwitchToLogin, onAuthenticated]);

  const handleAccountTypeChange = (nextType: "student" | "company") => {
    setAccountType(nextType);
    onAccountTypeChange?.(nextType);
  };

  const title = t(
    accountType === "student"
      ? "register.studentTitle"
      : "register.companyTitle",
  );
  const subtitle = t(
    accountType === "student"
      ? "register.studentSubtitle"
      : "register.companySubtitle",
  );

  return (
    <AuthLayout
      variant="register"
      title={title}
      subtitle={subtitle}
      form={
        <div className="account-type-switcher">
          <div className="account-toggle">
            <button
              type="button"
              className={accountType === "student" ? "active" : ""}
              onClick={() => handleAccountTypeChange("student")}
            >
              {t("register.student")}
            </button>
            <button
              type="button"
              className={accountType === "company" ? "active" : ""}
              onClick={() => handleAccountTypeChange("company")}
            >
              {t("register.company")}
            </button>
          </div>
          {form}
        </div>
      }
    />
  );
}
