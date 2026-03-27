import { ref } from "vue";

const TOKEN_KEY = "watch-shop-admin-token";
const USERNAME_KEY = "watch-shop-admin-username";

function readStorage(key: string): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

export const adminToken = ref(readStorage(TOKEN_KEY));
export const adminUsername = ref(readStorage(USERNAME_KEY));
export const authChecked = ref(!adminToken.value);

export function getAdminToken(): string {
  return adminToken.value;
}

export function hasAdminToken(): boolean {
  return Boolean(adminToken.value);
}

export function setAdminSession(token: string, username: string): void {
  adminToken.value = token;
  adminUsername.value = username;
  authChecked.value = true;

  if (typeof window !== "undefined") {
    window.localStorage.setItem(TOKEN_KEY, token);
    window.localStorage.setItem(USERNAME_KEY, username);
  }
}

export function setAdminUsername(username: string): void {
  adminUsername.value = username;

  if (typeof window !== "undefined") {
    window.localStorage.setItem(USERNAME_KEY, username);
  }
}

export function clearAdminSession(): void {
  adminToken.value = "";
  adminUsername.value = "";
  authChecked.value = true;

  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USERNAME_KEY);
  }
}

export function resetAuthCheck(): void {
  authChecked.value = !adminToken.value;
}
