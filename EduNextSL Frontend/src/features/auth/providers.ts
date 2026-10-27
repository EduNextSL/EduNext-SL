import { fetchProviders, type Providers } from "../../api/auth";

let cached: Promise<Providers> | null = null;

/** Which social providers the server has configured (fetched once per page load). */
export function getProviders(): Promise<Providers> {
  cached ??= fetchProviders().catch((error: unknown) => {
    cached = null; // allow a retry on the next mount
    throw error;
  });
  return cached;
}
