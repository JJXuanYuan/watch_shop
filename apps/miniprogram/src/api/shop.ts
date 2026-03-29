import { request } from "./http";
import type {
  CategoryListResponse,
  CategoryItem,
  ProductDetail,
  ProductListResponse,
  ProductListItem,
  ProductStoryBlock,
} from "../types/shop";
import {
  normalizeCategoryName,
  normalizeDisplayText,
  normalizeStringList,
} from "../utils/text";
import { normalizeImageList, normalizeImageUrl } from "../utils/url";

interface ProductListParams {
  category_id?: number;
  keyword?: string;
  page?: number;
  page_size?: number;
}

type StoryBlockRecord = ProductStoryBlock & Record<string, unknown>;

function normalizeSlug(value: string | null | undefined): string {
  return typeof value === "string" ? value.trim() : "";
}

function pickNormalizedText(
  record: StoryBlockRecord,
  keys: string[],
): string | null {
  for (const key of keys) {
    const currentValue = record[key];
    if (typeof currentValue !== "string") {
      continue;
    }

    const normalizedValue = normalizeDisplayText(currentValue);
    if (normalizedValue) {
      return normalizedValue;
    }
  }

  return null;
}

function mapCategorySummary(category: ProductListItem["category"]): ProductListItem["category"] {
  return {
    ...category,
    name: normalizeCategoryName(category.name, category.slug),
    slug: normalizeSlug(category.slug),
  };
}

function mapProductListItem(product: ProductListItem): ProductListItem {
  const normalizedName =
    normalizeDisplayText(product.name)
    || normalizeDisplayText(product.title)
    || `商品 ${product.id}`;

  return {
    ...product,
    category: mapCategorySummary(product.category),
    name: normalizedName,
    title: normalizedName,
    subtitle: normalizeDisplayText(product.subtitle),
    cover_image: normalizeImageUrl(product.cover_image),
    short_title: normalizeDisplayText(product.short_title),
    hero_image: normalizeImageUrl(product.hero_image),
    selling_points: normalizeStringList(product.selling_points),
    material: normalizeDisplayText(product.material),
    crystal: normalizeDisplayText(product.crystal),
    movement_or_function: normalizeDisplayText(product.movement_or_function),
    power_reserve: normalizeDisplayText(product.power_reserve),
    water_resistance: normalizeDisplayText(product.water_resistance),
    strap_material: normalizeDisplayText(product.strap_material),
    banner_images: normalizeImageList(product.banner_images),
    story_blocks: mapStoryBlocks(product.story_blocks),
  };
}

function mapProductDetail(product: ProductDetail): ProductDetail {
  return {
    ...mapProductListItem(product),
    detail_content: normalizeDisplayText(product.detail_content),
    detail: normalizeDisplayText(product.detail),
    updated_at: product.updated_at,
    banner_images: normalizeImageList(product.banner_images),
    image_list: normalizeImageList(product.image_list),
    story_blocks: mapStoryBlocks(product.story_blocks),
  };
}

function mapCategoryItem(category: CategoryItem): CategoryItem {
  return {
    ...category,
    name: normalizeCategoryName(category.name, category.slug),
    slug: normalizeSlug(category.slug),
    cover_image: normalizeImageUrl(category.cover_image),
    cover_title: normalizeDisplayText(category.cover_title),
    cover_subtitle: normalizeDisplayText(category.cover_subtitle),
  };
}

function mapStoryBlocks(storyBlocks: ProductStoryBlock[] | null | undefined): ProductStoryBlock[] {
  if (!Array.isArray(storyBlocks)) {
    return [];
  }

  return storyBlocks
    .map((block) => {
      const rawBlock = block as StoryBlockRecord;

      return {
        title: pickNormalizedText(rawBlock, ["title", "t", "headline"]),
        subtitle: pickNormalizedText(rawBlock, ["subtitle", "s", "summary"]),
        content: pickNormalizedText(rawBlock, ["content", "c", "description", "body", "text"]),
        image: normalizeImageUrl(
          pickNormalizedText(rawBlock, ["image", "i", "img", "image_url"]) || "",
        ),
        label: pickNormalizedText(rawBlock, ["label", "l", "kicker", "tag"]),
      };
    })
    .filter((block) => (
      Boolean(block.title)
      || Boolean(block.subtitle)
      || Boolean(block.content)
      || Boolean(block.image)
      || Boolean(block.label)
    ));
}

export function fetchCategories(): Promise<CategoryListResponse> {
  return request<CategoryListResponse>({
    url: "/categories",
  }).then((response) => ({
    ...response,
    items: response.items.map((item) => mapCategoryItem(item)),
  }));
}

export async function fetchProducts(
  params: ProductListParams = {},
): Promise<ProductListResponse> {
  const response = await request<ProductListResponse>({
    url: "/products",
    data: params as Record<string, unknown>,
  });

  return {
    ...response,
    items: response.items.map((item) => mapProductListItem(item)),
  };
}

export async function fetchProductDetail(productId: number): Promise<ProductDetail> {
  const response = await request<ProductDetail>({
    url: `/products/${productId}`,
  });

  return mapProductDetail(response);
}
