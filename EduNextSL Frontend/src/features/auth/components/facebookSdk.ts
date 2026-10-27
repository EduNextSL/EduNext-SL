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
  }
}

const SDK_SRC = "https://connect.facebook.net/en_US/sdk.js";
let sdkPromise: Promise<FacebookSdk> | null = null;

/** Load and initialise the Facebook JS SDK once. */
export function loadFacebookSdk(appId: string): Promise<FacebookSdk> {
  sdkPromise ??= new Promise<FacebookSdk>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SDK_SRC;
    script.async = true;
    script.onload = () => {
      if (!window.FB) return reject(new Error("Facebook SDK unavailable"));
      window.FB.init({ appId, cookie: false, xfbml: false, version: "v23.0" });
      resolve(window.FB);
    };
    script.onerror = () => {
      sdkPromise = null; // allow a later retry
      script.remove();
      reject(new Error("Facebook SDK failed to load"));
    };
    document.head.appendChild(script);
  });
  return sdkPromise;
}

export type { FacebookLoginResponse, FacebookSdk };
