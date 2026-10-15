import { AuthLayout } from "../components/AuthLayout";
import { LoginForm } from "../components/LoginForm";
import { useTranslation } from "react-i18next";

type LoginPageProps = {
  onSwitchToRegister: () => void;
};

export function LoginPage({ onSwitchToRegister }: LoginPageProps) {
  const { t } = useTranslation();

  return (
    <AuthLayout
      title={t("login.title")}
      subtitle={t("login.subtitle")}
      form={<LoginForm onSwitchToRegister={onSwitchToRegister} />}
    />
  );
}
