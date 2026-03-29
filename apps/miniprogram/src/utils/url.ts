import { API_ORIGIN } from "../api/client";

const PLACEHOLDER_IMAGE_URL_PATTERN = /^https?:\/\/images\.example\.com(\/|$)/i;

export function normalizeImageUrl(value: string | null | undefined): string {
  const rawValue = typeof value === "string" ? value.trim() : "";
  if (!rawValue) {
    return "";
  }

  if (/^\/\//.test(rawValue)) {
    return `https:${rawValue}`;
  }

  if (/^https?:\/\//i.test(rawValue)) {
    return PLACEHOLDER_IMAGE_URL_PATTERN.test(rawValue) ? "" : rawValue;
  }

  const normalizedPath = rawValue.startsWith("/") ? rawValue : `/${rawValue}`;
  return `${API_ORIGIN}${normalizedPath}`;
}

export function normalizeImageList(values: string[] | null | undefined): string[] {
  if (!Array.isArray(values)) {
    return [];
  }

  return values
    .map((value) => normalizeImageUrl(value))
    .filter((value) => Boolean(value));
}
