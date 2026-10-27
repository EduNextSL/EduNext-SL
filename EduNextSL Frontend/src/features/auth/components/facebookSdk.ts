type FacebookLoginResponse = {
  status: string;
  authResponse?: { accessToken: string } | null;
};

type FacebookSdk = {
  init: (config: {
    appId: string;
    cookie: boolean;
    xfbml: boolean;
    version: string;
  }) => void;
  login: (
    callback: (response: FacebookLoginResponse) => void,
    options: { scope: string },
  ) => void;
};

declare global {
  interface Window {
    FB?: FacebookSdk;
    fbAsyncInit?: () => void;
  }
}

const SDK_SRC = "https://connect.facebook.net/en_US/sdk.js";
let sdkPromise: Promise<void> | null = null;

/**
 * Load and initialise the Facebook JS SDK once.
 *
 * Facebook's script loads a second bundle after it fires `onload`, so the SDK is only
 * usable once it calls `window.fbAsyncInit`. Initialising earlier leaves `FB.login`
 * inert, which is why readiness is signalled from that callback.
 */
export function loadFacebookSdk(appId: string): Promise<void> {
  sdkPromise ??= new Promise<void>((resolve, reject) => {
    window.fbAsyncInit = () => {
      if (!window.FB) return reject(new Error("Facebook SDK unavailable"));
      window.FB.init({ appId, cookie: false, xfbml: false, version: "v23.0" });
      resolve();
    };
    const script = document.createElement("script");
    script.src = SDK_SRC;
    script.async = true;
    script.onerror = () => {
      sdkPromise = null; // allow a later retry
      script.remove();
      reject(new Error("Facebook SDK failed to load"));
    };
    document.head.appendChild(script);
  });
  return sdkPromise;
}

/** Open the Facebook login popup. Must be called directly from a click handler. */
export function facebookLogin(
  callback: (response: FacebookLoginResponse) => void,
): boolean {
  if (!window.FB) return false;
  window.FB.login(callback, { scope: "public_profile,email" });
  return true;
}

export type { FacebookLoginResponse, FacebookSdk };
