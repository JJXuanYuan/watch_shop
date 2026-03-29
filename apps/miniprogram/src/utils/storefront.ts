import type { CategoryItem, ProductListItem } from "../types/shop";

export type StoreChannelKey = "modeling" | "design" | "game" | "flash";

export interface StoreChannelDefinition {
  key: StoreChannelKey;
  label: string;
  subtitle: string;
  badge: string;
  heroLabel: string;
  searchPlaceholder: string;
}

const PRIMARY_CHANNEL_KEYS: StoreChannelKey[] = ["modeling", "design", "game"];

export const STOREFRONT_CHANNELS: StoreChannelDefinition[] = [
  {
    key: "modeling",
    label: "三维建模",
    subtitle: "聚焦主视觉和高辨识度商品表达",
    badge: "3D",
    heroLabel: "主推频道",
    searchPlaceholder: "搜索三维建模商品",
  },
  {
    key: "design",
    label: "智能设计",
    subtitle: "强调质感、效率和实用卖点",
    badge: "AI",
    heroLabel: "精选频道",
    searchPlaceholder: "搜索智能设计商品",
  },
  {
    key: "game",
    label: "游戏制作",
    subtitle: "承接更年轻、更轻快的陈列节奏",
    badge: "GM",
    heroLabel: "趋势频道",
    searchPlaceholder: "搜索游戏制作商品",
  },
  {
    key: "flash",
    label: "限时秒杀",
    subtitle: "汇总折扣感更强和更适合首屏主推的商品",
    badge: "HOT",
    heroLabel: "限时推荐",
    searchPlaceholder: "搜索限时秒杀商品",
  },
];

function normalizeText(value: string | null | undefined): string {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function ensureCategoryOrder(categories: CategoryItem[]): CategoryItem[] {
  return [...categories].sort((left, right) => left.sort_order - right.sort_order);
}

function buildSearchSource(product: ProductListItem): string {
  const sellingPoints = Array.isArray(product.selling_points)
    ? product.selling_points.join(" ")
    : product.selling_points ?? "";

  return [
    product.name,
    product.title,
    product.short_title,
    product.subtitle,
    product.category.name,
    sellingPoints,
    product.material,
    product.crystal,
    product.movement_or_function,
    product.power_reserve,
    product.water_resistance,
    product.strap_material,
  ]
    .map((item) => normalizeText(typeof item === "string" ? item : ""))
    .filter(Boolean)
    .join(" ");
}

function buildProductScore(product: ProductListItem, flashMode = false): number {
  const priceValue = Number(product.price ?? 0) || 0;
  const originalPriceValue = Number(product.original_price ?? 0) || 0;
  const discountScore =
    originalPriceValue > priceValue ? Math.round((originalPriceValue - priceValue) * 100) : 0;

  return (
    (flashMode ? 3 : 2) * Number(product.is_featured)
    + (flashMode ? 4 : 3) * discountScore
    + 12 * product.sales
    + Math.max(product.stock, 0)
  );
}

export function getDefaultChannelKey(value?: string | null): StoreChannelKey {
  const normalizedValue = normalizeText(value);
  const matchedChannel = STOREFRONT_CHANNELS.find((item) => item.key === normalizedValue);
  return matchedChannel?.key ?? "modeling";
}

export function getStoreChannelDefinition(channelKey: StoreChannelKey): StoreChannelDefinition {
  return STOREFRONT_CHANNELS.find((item) => item.key === channelKey) ?? STOREFRONT_CHANNELS[0];
}

export function resolveChannelCategory(
  channelKey: StoreChannelKey,
  categories: CategoryItem[],
): CategoryItem | null {
  const orderedCategories = ensureCategoryOrder(categories);
  if (channelKey === "flash") {
    return null;
  }

  const index = PRIMARY_CHANNEL_KEYS.indexOf(channelKey);
  if (index < 0) {
    return orderedCategories[0] ?? null;
  }

  return orderedCategories[index] ?? orderedCategories[0] ?? null;
}

export function getChannelProducts(
  channelKey: StoreChannelKey,
  products: ProductListItem[],
  categories: CategoryItem[],
): ProductListItem[] {
  const matchedCategory = resolveChannelCategory(channelKey, categories);
  const scopedProducts = matchedCategory
    ? products.filter((item) => item.category_id === matchedCategory.id)
    : [...products];
  const flashMode = channelKey === "flash";

  return scopedProducts
    .sort((left, right) => {
      const scoreGap = buildProductScore(right, flashMode) - buildProductScore(left, flashMode);
      if (scoreGap !== 0) {
        return scoreGap;
      }

      return left.id - right.id;
    });
}

export function filterProductsByKeyword(
  products: ProductListItem[],
  keyword: string,
): ProductListItem[] {
  const normalizedKeyword = normalizeText(keyword);
  if (!normalizedKeyword) {
    return products;
  }

  return products.filter((product) => buildSearchSource(product).includes(normalizedKeyword));
}

export function getChannelPageTitle(
  channelKey: StoreChannelKey,
  categories: CategoryItem[],
): string {
  const channel = getStoreChannelDefinition(channelKey);
  const matchedCategory = resolveChannelCategory(channelKey, categories);
  if (matchedCategory) {
    return `${channel.label} / ${matchedCategory.name}`;
  }

  return channel.label;
}
