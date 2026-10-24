import { useTranslation } from "react-i18next";

export function LoadingScreen() {
  const { t } = useTranslation();
  return (
    <main className="status-screen" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p>{t("auth.loading")}</p>
    </main>
  );
}

export function ErrorScreen({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  const { t } = useTranslation();
  return (
    <main className="status-screen" role="alert">
      <h1>{t("auth.connectionProblem")}</h1>
      <p>{message}</p>
      <div className="status-actions">
        <button
          type="button"
          className="primary-button status-button"
          onClick={onRetry}
        >
          {t("auth.tryAgain")}
        </button>
      </div>
    </main>
  );
}
