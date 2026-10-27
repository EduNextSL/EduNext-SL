import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { loginWithSocial, type SocialProvider, type User } from "../../../api/auth";
import { ApiError } from "../../../api/client";
import { getProviders } from "../providers";
import { FacebookButton } from "./FacebookButton";
import { GoogleButton } from "./GoogleButton";

type SocialButtonsProps = {
  /** Value of the page's terms checkbox, sent when the sign-in creates an account. */
  termsAccepted?: boolean;
  rememberMe?: boolean;
  split?: boolean;
  onSignedIn: (user: User) => void;
};

type Pending = { provider: SocialProvider; credential: string };

/** Google + Facebook buttons with shared sign-in, terms prompt and error handling. */
export function SocialButtons({
  termsAccepted = false,
  rememberMe = false,
  split = false,
  onSignedIn,
}: SocialButtonsProps) {
  const { t } = useTranslation();
  const [googleId, setGoogleId] = useState<string | null | undefined>(undefined);
  const [facebookId, setFacebookId] = useState<string | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [pendingTerms, setPendingTerms] = useState(false);

  useEffect(() => {
    let active = true;
    getProviders()
      .then((providers) => {
        if (!active) return;
        setGoogleId(providers.google?.client_id ?? null);
        setFacebookId(providers.facebook?.client_id ?? null);
      })
      .catch(() => {
        if (!active) return;
        setGoogleId(null);
        setFacebookId(null);
      });
    return () => {
      active = false;
    };
  }, []);

  const signIn = useCallback(
    async (provider: SocialProvider, credential: string, terms: boolean) => {
      setBusy(true);
      setError(null);
      try {
        onSignedIn(await loginWithSocial(provider, credential, terms, rememberMe));
      } catch (err) {
        if (err instanceof ApiError && err.code === "TERMS_REQUIRED") {
          setPending({ provider, credential });
        } else {
          setError(err instanceof ApiError ? err.message : t("auth.genericError"));
        }
      } finally {
        setBusy(false);
      }
    },
    [onSignedIn, rememberMe, t],
  );

  const handleGoogle = useCallback(
    (credential: string) => void signIn("google", credential, termsAccepted),
    [signIn, termsAccepted],
  );
  const handleFacebook = useCallback(
    (credential: string) => void signIn("facebook", credential, termsAccepted),
    [signIn, termsAccepted],
  );

  return (
    <>
      <div className={split ? "social-login-row social-login-row--split" : "social-login-row"}>
        <GoogleButton clientId={googleId} onCredential={handleGoogle} onError={setError} />
        <FacebookButton
          appId={facebookId}
          disabled={busy}
          onCredential={handleFacebook}
          onError={setError}
        />
      </div>

      {pending && (
        <div className="google-terms" role="group">
          <label className="terms-row">
            <input
              type="checkbox"
              checked={pendingTerms}
              onChange={(event) => setPendingTerms(event.target.checked)}
            />
            <span>{t("auth.socialTermsPrompt")}</span>
          </label>
          <button
            type="button"
            className="primary-button status-button"
            disabled={!pendingTerms || busy}
            onClick={() => {
              const current = pending;
              setPending(null);
              void signIn(current.provider, current.credential, true);
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
    </>
  );
}
