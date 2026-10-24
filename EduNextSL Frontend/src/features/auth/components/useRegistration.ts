import { useState } from "react";
import { useTranslation } from "react-i18next";
import { login, type User } from "../../../api/auth";
import { ApiError, type FieldErrors } from "../../../api/client";

/**
 * Shared submit logic for the student and company forms: sends the registration,
 * signs the new user in, and surfaces server-side field errors.
 */
export function useRegistration(options: {
  register: () => Promise<unknown>;
  email: string;
  password: string;
  onAuthenticated: (user: User) => void;
  onSwitchToLogin: () => void;
}) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);

  async function submit() {
    if (busy) return; // ignore double submits
    setBusy(true);
    setFieldErrors({});
    setFormError(null);
    try {
      await options.register();
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldErrors(err.fieldErrors);
        if (Object.keys(err.fieldErrors).length === 0) setFormError(err.message);
      } else {
        setFormError(t("auth.genericError"));
      }
      setBusy(false);
      return;
    }
    try {
      options.onAuthenticated(await login(options.email, options.password, false));
    } catch {
      // Account exists but automatic sign-in failed; let the user sign in manually.
      options.onSwitchToLogin();
    }
  }

  return { busy, fieldErrors, formError, submit };
}

export function firstError(errors: FieldErrors, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const message = errors[key]?.[0];
    if (message) return message;
  }
  return undefined;
}
