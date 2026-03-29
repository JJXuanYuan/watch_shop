import type {
  CategoryItem,
  ProductDetail,
  ProductListItem,
  ProductStoryBlock,
} from "../types/shop";

type ProductContentSource = Partial<
  Pick<
    ProductListItem,
    | "id"
    | "category_id"
    | "category"
    | "name"
    | "title"
    | "subtitle"
    | "short_title"
    | "cover_image"
    | "hero_image"
    | "banner_images"
    | "selling_points"
    | "material"
    | "crystal"
    | "movement_or_function"
    | "power_reserve"
    | "water_resistance"
    | "strap_material"
    | "stock"
    | "sales"
    | "status"
    | "is_featured"
    | "story_blocks"
  >
> &
  Partial<Pick<ProductDetail, "detail_content" | "detail" | "image_list">>;

export interface ProductSpecEntry {
  key: string;
  label: string;
  value: string;
}

export interface ProductStorySection {
  kicker: string;
  title: string;
  summary: string;
  image: string;
}

export interface CategoryCoverProfile {
  image: string;
  imageCandidates: string[];
  title: string;
  subtitle: string;
  material: string;
  accent: string;
}

export interface ProductContentBundle {
  shortTitle: string;
  subtitle: string;
  heroImage: string;
  galleryImages: string[];
  sellingPoints: string[];
  specs: ProductSpecEntry[];
  storyBlocks: ProductStorySection[];
  categoryCover: CategoryCoverProfile | null;
}

function ensureText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function pickSourceText(product: ProductContentSource): string {
  return [
    product.short_title,
    product.title,
    product.name,
    product.subtitle,
    product.detail_content,
    product.detail,
  ]
    .map((item) => ensureText(item))
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function matchKeyword(source: string, keywords: string[]): boolean {
  return keywords.some((keyword) => source.includes(keyword));
}

function uniqueImages(values: Array<string | null | undefined>): string[] {
  return values
    .map((item) => ensureText(item))
    .filter((item, index, list) => Boolean(item) && list.indexOf(item) === index);
}

function parseStringList(value: string[] | string | null | undefined): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => ensureText(item)).filter(Boolean);
  }

  const rawValue = ensureText(value);
  if (!rawValue) {
    return [];
  }

  return rawValue
    .split(/[\n,，/|、]+/)
    .map((item) => ensureText(item))
    .filter(Boolean);
}

function buildFallbackSummary(product: ProductContentSource): string {
  if (ensureText(product.detail_content)) {
    return ensureText(product.detail_content).split(/[\n。！？]/)[0];
  }

  return product.is_featured
    ? "以更纯粹的轮廓、材质与盘面比例，呈现这一系列的主视觉表达。"
    : "为日常通勤与正式场景准备的高端腕表选择。";
}

function buildFallbackSellingPoints(product: ProductContentSource): string[] {
  const source = pickSourceText(product);
  const points = [
    matchKeyword(source, ["sapphire", "蓝宝石"]) ? "蓝宝石镜面" : "立体镜面光泽",
    matchKeyword(source, ["smart", "智能"]) ? "多功能智能表盘" : "精致盘面布局",
    (product.stock ?? 0) > 0 && (product.stock ?? 0) <= 20 ? "少量现货" : "常备现货",
  ];

  if (matchKeyword(source, ["sport", "运动", "chrono", "计时"])) {
    points[1] = "多功能计时布局";
  }

  if (product.is_featured) {
    points[0] = "旗舰系列";
  }

  return points;
}

function buildFallbackSpecMap(product: ProductContentSource): Record<string, string> {
  const source = pickSourceText(product);
  const isSmart = matchKeyword(source, ["smart", "智能"]);
  const isSport = matchKeyword(source, ["sport", "运动", "chrono", "计时"]);

  return {
    material: matchKeyword(source, ["titanium", "钛"])
      ? "钛金属表壳"
      : matchKeyword(source, ["ceramic", "陶瓷"])
        ? "陶瓷复合表圈"
        : "316L 精钢表壳",
    crystal: matchKeyword(source, ["sapphire", "蓝宝石"])
      ? "双面蓝宝石玻璃"
      : "强化镜面玻璃",
    movement_or_function: isSmart
      ? "多功能智能模组"
      : isSport
        ? "多功能计时机芯"
        : "自动机械机芯",
    power_reserve: isSmart ? "14 天综合续航" : isSport ? "72 小时动力储备" : "80 小时动力储备",
    water_resistance: isSport ? "100 米防水" : isSmart ? "50 米防水" : "80 米防水",
    strap_material: matchKeyword(source, ["leather", "皮"])
      ? "真皮表带"
      : matchKeyword(source, ["steel", "精钢", "bracelet"])
        ? "精钢表链"
        : isSport
          ? "氟橡胶表带"
          : "复合材质表带",
  };
}

function resolveSpecs(product: ProductContentSource): ProductSpecEntry[] {
  const fallback = buildFallbackSpecMap(product);
  const specConfig = [
    { key: "material", label: "材质", backend: ensureText(product.material) },
    { key: "crystal", label: "镜面", backend: ensureText(product.crystal) },
    {
      key: "movement_or_function",
      label: "机芯/功能",
      backend: ensureText(product.movement_or_function),
    },
    { key: "power_reserve", label: "动力储备", backend: ensureText(product.power_reserve) },
    {
      key: "water_resistance",
      label: "防水等级",
      backend: ensureText(product.water_resistance),
    },
    {
      key: "strap_material",
      label: "表带材质",
      backend: ensureText(product.strap_material),
    },
  ];

  return specConfig.map((item) => ({
    key: item.key,
    label: item.label,
    value: item.backend || fallback[item.key],
  }));
}

function buildFallbackCategoryAccent(
  category: Pick<CategoryItem, "name" | "slug">,
  leadProduct?: ProductContentSource | null,
): Pick<CategoryCoverProfile, "material" | "accent" | "subtitle"> {
  const source =
    `${category.name} ${category.slug} ${leadProduct?.short_title || ""} ${leadProduct?.title || ""} ${leadProduct?.name || ""}`.toLowerCase();

  if (matchKeyword(source, ["sport", "运动", "chrono", "计时"])) {
    return {
      material: "Ceramic",
      subtitle: "强化运动计时与耐候佩戴感的系列导购。",
      accent: "速度与轮廓",
    };
  }

  if (matchKeyword(source, ["smart", "智能"])) {
    return {
      material: "Titanium",
      subtitle: "偏向智能交互和轻量佩戴体验的系列导购。",
      accent: "连接与效率",
    };
  }

  if (matchKeyword(source, ["classic", "经典", "商务"])) {
    return {
      material: "Leather",
      subtitle: "更偏正式佩戴与传统表盘语汇的系列导购。",
      accent: "经典与秩序",
    };
  }

  return {
    material: "Brushed Steel",
    subtitle: "以材质光泽和比例轮廓作为主导的系列陈列。",
    accent: "质感与佩戴",
  };
}

function resolveStoryBlocks(product: ProductContentSource): ProductStorySection[] {
  const galleryImages = resolveGalleryImages(product);
  const backendBlocks = Array.isArray(product.story_blocks) ? product.story_blocks : [];

  if (backendBlocks.length) {
    const normalizedBlocks = backendBlocks
      .map((block, index) => normalizeStoryBlock(block, galleryImages[index] || galleryImages[0] || ""))
      .filter((block) => block.summary || block.image);

    if (normalizedBlocks.length) {
      return normalizedBlocks;
    }
  }

  const specs = resolveSpecs(product);
  const summary = ensureText(product.detail_content) || buildFallbackSummary(product);
  const detailCopy = ensureText(product.detail) || summary;

  return [
    {
      kicker: "产品概览",
      title: resolveShortTitle(product),
      summary,
      image: galleryImages[0] || "",
    },
    {
      kicker: "规格亮点",
      title: specs.slice(0, 2).map((item) => item.value).join(" / ") || "高端佩戴体验",
      summary: detailCopy,
      image: galleryImages[1] || galleryImages[0] || "",
    },
  ].filter((block) => block.summary || block.image);
}

function normalizeStoryBlock(block: ProductStoryBlock, fallbackImage: string): ProductStorySection {
  const title = ensureText(block.title) || ensureText(block.label) || "细节亮点";
  const summary = ensureText(block.content) || ensureText(block.subtitle);
  return {
    kicker: ensureText(block.label) || "产品叙事",
    title,
    summary,
    image: ensureText(block.image) || fallbackImage,
  };
}

function resolveShortTitle(product: ProductContentSource): string {
  return ensureText(product.short_title) || ensureText(product.title) || ensureText(product.name);
}

function resolveSubtitle(product: ProductContentSource): string {
  return ensureText(product.subtitle) || buildFallbackSummary(product);
}

function resolveHeroImage(product: ProductContentSource): string {
  return (
    ensureText(product.hero_image)
    || uniqueImages(product.banner_images ?? [])[0]
    || ensureText(product.cover_image)
    || uniqueImages(product.image_list ?? [])[0]
    || ""
  );
}

function resolveGalleryImages(product: ProductContentSource): string[] {
  return uniqueImages([
    ensureText(product.hero_image),
    ...uniqueImages(product.banner_images ?? []),
    ...uniqueImages(product.image_list ?? []),
    ensureText(product.cover_image),
  ]);
}

function resolveSellingPoints(product: ProductContentSource): string[] {
  const backendPoints = parseStringList(product.selling_points);
  if (backendPoints.length) {
    return backendPoints.slice(0, 4);
  }

  return buildFallbackSellingPoints(product);
}

export function getCategoryCoverProfile(
  category: Pick<CategoryItem, "name" | "slug" | "cover_image" | "cover_title" | "cover_subtitle">,
  leadProduct?: ProductContentSource | null,
): CategoryCoverProfile {
  const fallback = buildFallbackCategoryAccent(category, leadProduct);
  const leadImages = leadProduct ? resolveGalleryImages(leadProduct) : [];
  const imageCandidates = uniqueImages([
    ensureText(category.cover_image),
    ...leadImages,
  ]);

  return {
    image: imageCandidates[0] || "",
    imageCandidates,
    title: ensureText(category.cover_title) || ensureText(category.name) || "腕表系列",
    subtitle: ensureText(category.cover_subtitle) || fallback.subtitle,
    material: fallback.material,
    accent: fallback.accent,
  };
}

export function getProductContent(
  product: ProductContentSource,
  category?: Pick<CategoryItem, "name" | "slug" | "cover_image" | "cover_title" | "cover_subtitle"> | null,
): ProductContentBundle {
  const shortTitle = resolveShortTitle(product);
  const subtitle = resolveSubtitle(product);
  const heroImage = resolveHeroImage(product);
  const galleryImages = resolveGalleryImages(product);
  const sellingPoints = resolveSellingPoints(product);
  const specs = resolveSpecs(product);
  const storyBlocks = resolveStoryBlocks(product);

  return {
    shortTitle,
    subtitle,
    heroImage,
    galleryImages,
    sellingPoints,
    specs,
    storyBlocks,
    categoryCover: category ? getCategoryCoverProfile(category, product) : null,
  };
}

export function getProductDisplayTitle(product: ProductContentSource): string {
  return getProductContent(product).shortTitle;
}

export function getProductDisplaySummary(product: ProductContentSource): string {
  return getProductContent(product).subtitle;
}

export function getProductHeroImage(product: ProductContentSource): string {
  return getProductContent(product).heroImage;
}

export function getProductGalleryImages(product: ProductContentSource): string[] {
  return getProductContent(product).galleryImages;
}

export function getProductSellingPoints(product: ProductContentSource): string[] {
  return getProductContent(product).sellingPoints;
}

export function getProductSpecEntries(product: ProductContentSource): ProductSpecEntry[] {
  return getProductContent(product).specs;
}

export function getProductStoryBlocks(product: ProductContentSource): ProductStorySection[] {
  return getProductContent(product).storyBlocks;
}
