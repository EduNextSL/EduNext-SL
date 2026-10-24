import { request, setAccessToken } from "./client";

export type Role =
  | "student"
  | "employer"
  | "instructor"
  | "moderator"
  | "administrator";

export type User = {
  id: string;
  email: string;
  role: Role;
  status: string;
  profile:
    | { first_name: string; last_name: string }
    | {
        id: string;
        name: string;
        contact_full_name: string;
        work_email: string;
        verification_status: string;
      }
    | null;
};

type Session = { access: string; access_expires_in: number; user: User };

export type StudentRegistration = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  password_confirm: string;
  terms_accepted: boolean;
};

export type CompanyRegistration = {
  company_name: string;
  contact_full_name: string;
  work_email: string;
  password: string;
  password_confirm: string;
  terms_accepted: boolean;
};

export type Providers = {
  google: { client_id: string } | null;
  facebook: { client_id: string } | null;
};

async function startSession(promise: Promise<Session>): Promise<User> {
  const session = await promise;
  setAccessToken(session.access);
  return session.user;
}

export function login(email: string, password: string, rememberMe: boolean) {
  return startSession(
    request<Session>("/auth/login/", {
      method: "POST",
      body: { email, password, remember_me: rememberMe },
    }),
  );
}

export function loginWithGoogle(
  credential: string,
  termsAccepted: boolean,
  rememberMe: boolean,
) {
  return startSession(
    request<Session>("/auth/social/google/", {
      method: "POST",
      body: { credential, terms_accepted: termsAccepted, remember_me: rememberMe },
    }),
  );
}

export function registerStudent(payload: StudentRegistration) {
  return request<{ user: User }>("/auth/register/student/", {
    method: "POST",
    body: payload,
  });
}

export function registerCompany(payload: CompanyRegistration) {
  return request<{ user: User }>("/auth/register/company/", {
    method: "POST",
    body: payload,
  });
}

export async function fetchCurrentUser(): Promise<User> {
  const data = await request<{ user: User }>("/auth/me/", { auth: true });
  return data.user;
}

export async function logout() {
  try {
    await request<void>("/auth/logout/", { method: "POST" });
  } finally {
    setAccessToken(null);
  }
}

export function requestPasswordReset(email: string) {
  return request<Record<string, never>>("/auth/password-reset/request/", {
    method: "POST",
    body: { email },
  });
}

export function confirmPasswordReset(
  uid: string,
  token: string,
  newPassword: string,
  newPasswordConfirm: string,
) {
  return request<Record<string, never>>("/auth/password-reset/confirm/", {
    method: "POST",
    body: {
      uid,
      token,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    },
  });
}

export function fetchProviders() {
  return request<Providers>("/auth/providers/");
}
