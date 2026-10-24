import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/authContext";

function displayName(profile: unknown, fallback: string): string {
  const p = profile as Record<string, string> | null;
  if (p?.first_name) return `${p.first_name} ${p.last_name ?? ""}`.trim();
  if (p?.name) return p.name;
  return fallback;
}

/** Placeholder landing page after sign-in; real dashboard content comes later. */
export function DashboardPage() {
  const { t } = useTranslation();
  const { user, signOut } = useAuth();
  if (!user) return null;

  return (
    <main className="dashboard">
      <h1>{t("auth.welcome", { name: displayName(user.profile, user.email) })}</h1>
      <dl>
        <dt>{t("common.email")}</dt>
        <dd>{user.email}</dd>
        <dt>{t("auth.role")}</dt>
        <dd>{user.role}</dd>
        <dt>{t("auth.status")}</dt>
        <dd>{user.status}</dd>
      </dl>
      <button
        type="button"
        className="primary-button status-button"
        onClick={() => void signOut()}
      >
        {t("auth.logout")}
      </button>
    </main>
  );
}
