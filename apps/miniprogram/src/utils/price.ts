import type { MoneyValue } from "../types/shop";

export function formatPrice(value: MoneyValue): string {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  const numericValue = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numericValue)) {
    return "--";
  }

  return numericValue.toFixed(2);
}

export function hasPrice(value: MoneyValue): boolean {
  if (value === null || value === undefined || value === "") {
    return false;
  }

  return !Number.isNaN(typeof value === "number" ? value : Number(value));
}
