import { useEffect, useRef } from "react";
import { FcGoogle } from "react-icons/fc";
import { useTranslation } from "react-i18next";

type GoogleIdentity = {
  initialize: (config: {
    client_id: string;
    callback: (response: { credential: string }) => void;
  }) => void;
  renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
};

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdentity } };
  }
}

const GSI_SRC = "https://accounts.google.com/gsi/client";
let gsiPromise: Promise<void> | null = null;

function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts) return Promise.resolve();
  gsiPromise ??= new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = GSI_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      gsiPromise = null; // allow a later retry
      script.remove();
      reject(new Error("Google script failed to load"));
    };
    document.head.appendChild(script);
  });
  return gsiPromise;
}

type GoogleButtonProps = {
  /** undefined = still asking the server, null = Google sign-in is not configured. */
  clientId: string | null | undefined;
  onCredential: (idToken: string) => void;
  onError: (message: string) => void;
};

export function GoogleButton({ clientId, onCredential, onError }: GoogleButtonProps) {
  const { t } = useTranslation();
  const hostRef = useRef<HTMLDivElement>(null);
  // The GIS callback is registered once, so it reads the latest handler through a ref.
  const onCredentialRef = useRef(onCredential);
  useEffect(() => {
    onCredentialRef.current = onCredential;
  });

  useEffect(() => {
    if (!clientId || !hostRef.current) return;
    let active = true;
    const host = hostRef.current;
    loadGoogleScript()
      .then(() => {
        if (!active || !window.google) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: ({ credential }) => onCredentialRef.current(credential),
        });
        window.google.accounts.id.renderButton(host, {
          type: "icon",
          shape: "circle",
          theme: "outline",
          size: "large",
        });
      })
      .catch(() => active && onError(t("auth.googleLoadFailed")));
    return () => {
      active = false;
      host.replaceChildren();
    };
  }, [clientId, onError, t]);

  if (clientId) {
    return (
      <div
        ref={hostRef}
        className="google-button-host"
        aria-label={t("login.google")}
      />
    );
  }
  return (
    <button
      type="button"
      className="social-button social-button--google"
      disabled
      aria-label={t("login.google")}
      title={clientId === null ? t("auth.googleUnavailable") : undefined}
    >
      <FcGoogle aria-hidden="true" />
    </button>
  );
}
