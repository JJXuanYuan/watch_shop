const MOJIBAKE_CHAR_PATTERN =
  /[\u0080-\u009f�]|Ã|Â|â|æ|ç|å|è|é|ê|ë|ï|ð|Ÿ|¢|€|™|‹|›|œ|ž|Ë/i;

const CATEGORY_NAME_FALLBACKS: Record<string, string> = {
  accessories: "表带配件",
  mechanical: "机械腕表",
  smartwatch: "智能腕表",
};

function normalizeWhitespace(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function getMojibakeScore(value: string): number {
  const matches = value.match(MOJIBAKE_CHAR_PATTERN);
  return matches ? matches.length : 0;
}

function decodeLatin1ToUtf8(value: string): string {
  const encoded = Array.from(value)
    .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, "0")}`)
    .join("");

  try {
    return decodeURIComponent(encoded);
  } catch {
    return value;
  }
}

export function normalizeDisplayText(value: string | null | undefined): string {
  const rawValue = typeof value === "string" ? normalizeWhitespace(value) : "";
  if (!rawValue) {
    return "";
  }

  let bestValue = rawValue;
  let bestScore = getMojibakeScore(bestValue);

  if (bestScore === 0) {
    return bestValue;
  }

  let currentValue = rawValue;

  for (let index = 0; index < 3; index += 1) {
    const decodedValue = normalizeWhitespace(decodeLatin1ToUtf8(currentValue));
    if (!decodedValue || decodedValue === currentValue) {
      break;
    }

    const decodedScore = getMojibakeScore(decodedValue);
    const isMoreReadable =
      decodedScore < bestScore
      || (/[\u4e00-\u9fff]/.test(decodedValue) && !/[\u4e00-\u9fff]/.test(bestValue));

    if (!isMoreReadable) {
      break;
    }

    bestValue = decodedValue;
    bestScore = decodedScore;
    currentValue = decodedValue;

    if (bestScore === 0) {
      break;
    }
  }

  return bestScore > 0 && MOJIBAKE_CHAR_PATTERN.test(bestValue) ? "" : bestValue;
}

export function normalizeStringList(
  value: string[] | string | null | undefined,
): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeDisplayText(item)).filter(Boolean);
  }

  const normalizedValue = normalizeDisplayText(value);
  if (!normalizedValue) {
    return [];
  }

  return normalizedValue
    .split(/[\n,，/|、]+/)
    .map((item) => normalizeDisplayText(item))
    .filter(Boolean);
}

export function normalizeCategoryName(
  name: string | null | undefined,
  slug: string | null | undefined,
): string {
  const normalizedName = normalizeDisplayText(name);
  if (normalizedName) {
    return normalizedName;
  }

  const normalizedSlug = typeof slug === "string" ? slug.trim().toLowerCase() : "";
  return CATEGORY_NAME_FALLBACKS[normalizedSlug] || "腕表系列";
}
