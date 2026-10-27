import { useEffect, useState } from "react";
import { FaFacebookF } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { loadFacebookSdk, type FacebookSdk } from "./facebookSdk";

type FacebookButtonProps = {
  /** undefined = still asking the server, null = Facebook sign-in is not configured. */
  appId: string | null | undefined;
  disabled?: boolean;
  onCredential: (accessToken: string) => void;
  onError: (message: string) => void;
};

export function FacebookButton({
  appId,
  disabled,
  onCredential,
  onError,
}: FacebookButtonProps) {
  const { t } = useTranslation();
  const [sdk, setSdk] = useState<FacebookSdk | null>(null);

  // The SDK is loaded ahead of the click: FB.login opens a popup, which browsers only
  // allow synchronously inside the click handler.
  useEffect(() => {
    if (!appId) return;
    let active = true;
    loadFacebookSdk(appId)
      .then((loaded) => active && setSdk(loaded))
      .catch(() => active && onError(t("auth.facebookLoadFailed")));
    return () => {
      active = false;
    };
  }, [appId, onError, t]);

  function handleClick() {
    sdk?.login(
      (response) => {
        const token = response.authResponse?.accessToken;
        if (token) onCredential(token);
        else onError(t("auth.facebookCancelled"));
      },
      { scope: "public_profile,email" },
    );
  }

  return (
    <button
      type="button"
      className="social-button social-button--facebook"
      aria-label={t("login.facebook")}
      title={appId === null ? t("auth.facebookUnavailable") : undefined}
      disabled={!sdk || disabled}
      onClick={handleClick}
    >
      <FaFacebookF aria-hidden="true" />
    </button>
  );
}
