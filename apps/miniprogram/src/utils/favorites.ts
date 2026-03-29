const FAVORITE_PRODUCTS_STORAGE_KEY = "watch_shop_favorite_products";
const MAX_FAVORITE_PRODUCTS = 32;

export interface FavoriteProductSnapshot {
  id: number;
  title: string;
  subtitle: string;
  coverImage: string;
  updatedAt: number;
}

function isFavoriteSnapshot(value: unknown): value is FavoriteProductSnapshot {
  if (!value || typeof value !== "object") {
    return false;
  }

  const payload = value as Partial<FavoriteProductSnapshot>;
  return (
    typeof payload.id === "number"
    && typeof payload.title === "string"
    && typeof payload.subtitle === "string"
    && typeof payload.coverImage === "string"
    && typeof payload.updatedAt === "number"
  );
}

function readFavoriteProducts(): FavoriteProductSnapshot[] {
  const storedValue = uni.getStorageSync(FAVORITE_PRODUCTS_STORAGE_KEY);
  if (!Array.isArray(storedValue)) {
    return [];
  }

  return storedValue.filter((item) => isFavoriteSnapshot(item));
}

function writeFavoriteProducts(items: FavoriteProductSnapshot[]): void {
  uni.setStorageSync(
    FAVORITE_PRODUCTS_STORAGE_KEY,
    items
      .slice(0, MAX_FAVORITE_PRODUCTS)
      .sort((left, right) => right.updatedAt - left.updatedAt),
  );
}

export function getFavoriteProducts(): FavoriteProductSnapshot[] {
  return readFavoriteProducts();
}

export function getFavoriteCount(): number {
  return readFavoriteProducts().length;
}

export function isFavoriteProduct(productId: number): boolean {
  return readFavoriteProducts().some((item) => item.id === productId);
}

export function toggleFavoriteProduct(
  snapshot: Omit<FavoriteProductSnapshot, "updatedAt">,
): boolean {
  const currentItems = readFavoriteProducts();
  const existingIndex = currentItems.findIndex((item) => item.id === snapshot.id);

  if (existingIndex >= 0) {
    currentItems.splice(existingIndex, 1);
    writeFavoriteProducts(currentItems);
    return false;
  }

  currentItems.unshift({
    ...snapshot,
    updatedAt: Date.now(),
  });
  writeFavoriteProducts(currentItems);
  return true;
}
