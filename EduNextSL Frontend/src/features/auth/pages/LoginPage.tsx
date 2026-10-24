import { useTranslation } from "react-i18next";
import type { User } from "../../../api/auth";
import { AuthLayout } from "../components/AuthLayout";
import { LoginForm } from "../components/LoginForm";

type LoginPageProps = {
  onSwitchToRegister: () => void;
  onForgotPassword: () => void;
  onAuthenticated: (user: User) => void;
};

export function LoginPage({
  onSwitchToRegister,
  onForgotPassword,
  onAuthenticated,
}: LoginPageProps) {
  const { t } = useTranslation();

  return (
    <AuthLayout
      title={t("login.title")}
      subtitle={t("login.subtitle")}
      form={
        <LoginForm
          onSwitchToRegister={onSwitchToRegister}
          onForgotPassword={onForgotPassword}
          onAuthenticated={onAuthenticated}
        />
      }
    />
  );
}
