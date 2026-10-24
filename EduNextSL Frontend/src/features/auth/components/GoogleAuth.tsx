import { useEffect, useRef, useState } from "react";
import { FcGoogle } from "react-icons/fc";
import { useTranslation } from "react-i18next";
import { fetchProviders, loginWithGoogle, type User } from "../../../api/auth";
import { ApiError } from "../../../api/client";

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

type GoogleAuthProps = {
  /** Value of the page's terms checkbox, sent when the sign-in creates an account. */
  termsAccepted?: boolean;
  rememberMe?: boolean;
  onSignedIn: (user: User) => void;
};

export function GoogleAuth({
  termsAccepted = false,
  rememberMe = false,
  onSignedIn,
}: GoogleAuthProps) {
  const { t } = useTranslation();
  const hostRef = useRef<HTMLDivElement>(null);
  // undefined = still asking the server, null = Google sign-in is not configured.
  const [clientId, setClientId] = useState<string | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [pendingCredential, setPendingCredential] = useState<string | null>(null);
  const [pendingTerms, setPendingTerms] = useState(false);
  const [busy, setBusy] = useState(false);

  // The GIS callback is registered once, so it reads current props through a ref.
  const latest = useRef({ termsAccepted, rememberMe, onSignedIn });
  useEffect(() => {
    latest.current = { termsAccepted, rememberMe, onSignedIn };
  });

  async function signIn(credential: string, terms: boolean) {
    setBusy(true);
    setError(null);
    try {
      const user = await loginWithGoogle(credential, terms, latest.current.rememberMe);
      latest.current.onSignedIn(user);
    } catch (err) {
      if (err instanceof ApiError && err.code === "TERMS_REQUIRED") {
        setPendingCredential(credential);
      } else {
        setError(err instanceof ApiError ? err.message : t("auth.genericError"));
      }
    } finally {
      setBusy(false);
    }
  }
  const signInRef = useRef(signIn);
  useEffect(() => {
    signInRef.current = signIn;
  });

  useEffect(() => {
    let active = true;
    fetchProviders()
      .then((providers) => active && setClientId(providers.google?.client_id ?? null))
      .catch(() => active && setClientId(null));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!clientId || !hostRef.current) return;
    let active = true;
    const host = hostRef.current;
    loadGoogleScript()
      .then(() => {
        if (!active || !window.google) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: ({ credential }) =>
            void signInRef.current(credential, latest.current.termsAccepted),
        });
        window.google.accounts.id.renderButton(host, {
          type: "icon",
          shape: "circle",
          theme: "outline",
          size: "large",
        });
      })
      .catch(() => active && setError(t("auth.googleLoadFailed")));
    return () => {
      active = false;
      host.replaceChildren();
    };
  }, [clientId, t]);

  return (
    <div className="google-auth">
      {clientId ? (
        <div
          ref={hostRef}
          className="google-button-host"
          aria-busy={busy}
          aria-label={t("login.google")}
        />
      ) : (
        <button
          type="button"
          className="social-button social-button--google"
          disabled
          aria-label={t("login.google")}
          title={clientId === null ? t("auth.googleUnavailable") : undefined}
        >
          <FcGoogle aria-hidden="true" />
        </button>
      )}

      {pendingCredential && (
        <div className="google-terms" role="group">
          <label className="terms-row">
            <input
              type="checkbox"
              checked={pendingTerms}
              onChange={(event) => setPendingTerms(event.target.checked)}
            />
            <span>{t("auth.googleTermsPrompt")}</span>
          </label>
          <button
            type="button"
            className="primary-button status-button"
            disabled={!pendingTerms || busy}
            onClick={() => {
              const credential = pendingCredential;
              setPendingCredential(null);
              void signIn(credential, true);
            }}
          >
            {t("auth.continue")}
          </button>
        </div>
      )}

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
