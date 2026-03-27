import { fetchAdminProfile } from "../api/auth";
import {
  authChecked,
  clearAdminSession,
  getAdminToken,
  hasAdminToken,
  setAdminUsername,
} from "./session";

let inflightVerification: Promise<boolean> | null = null;

export async function ensureAdminSession(): Promise<boolean> {
  if (!hasAdminToken()) {
    authChecked.value = true;
    return false;
  }

  if (authChecked.value) {
    return true;
  }

  if (inflightVerification) {
    return inflightVerification;
  }

  inflightVerification = fetchAdminProfile()
    .then((profile) => {
      if (!getAdminToken()) {
        return false;
      }

      setAdminUsername(profile.username);
      authChecked.value = true;
      return true;
    })
    .catch(() => {
      clearAdminSession();
      return false;
    })
    .finally(() => {
      inflightVerification = null;
    });

  return inflightVerification;
}
