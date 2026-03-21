from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Product, ProductCategory, ProductStatus

CATEGORY_SEEDS = [
    {"name": "电子表", "slug": "smartwatch", "sort_order": 1, "is_active": True},
    {"name": "机械表", "slug": "mechanical", "sort_order": 2, "is_active": True},
    {"name": "配件", "slug": "accessories", "sort_order": 3, "is_active": True},
]

PRODUCT_SEEDS = [
    {
        "category_slug": "smartwatch",
        "title": "Chronos S1 智能腕表",
        "subtitle": "全天候心率监测与双频 GPS",
        "cover_image": "https://images.example.com/products/chronos-s1-cover.jpg",
        "image_list": [
            "https://images.example.com/products/chronos-s1-1.jpg",
            "https://images.example.com/products/chronos-s1-2.jpg",
        ],
        "price": Decimal("1999.00"),
        "original_price": Decimal("2299.00"),
        "stock": 120,
        "sales": 58,
        "status": ProductStatus.ACTIVE,
        "is_featured": True,
        "detail": "旗舰级智能腕表，支持运动记录、睡眠分析和 NFC 便捷支付。",
    },
    {
        "category_slug": "smartwatch",
        "title": "Pulse Mini 轻量智能表",
        "subtitle": "轻薄机身，适合日常通勤佩戴",
        "cover_image": "https://images.example.com/products/pulse-mini-cover.jpg",
        "image_list": [
            "https://images.example.com/products/pulse-mini-1.jpg",
            "https://images.example.com/products/pulse-mini-2.jpg",
        ],
        "price": Decimal("999.00"),
        "original_price": Decimal("1299.00"),
        "stock": 240,
        "sales": 132,
        "status": ProductStatus.ACTIVE,
        "is_featured": False,
        "detail": "主打轻盈与长续航，适合日常健康监测和基础运动记录。",
    },
    {
        "category_slug": "mechanical",
        "title": "Voyager M 自动机械表",
        "subtitle": "蓝宝石镜面与 80 小时动储",
        "cover_image": "https://images.example.com/products/voyager-m-cover.jpg",
        "image_list": [
            "https://images.example.com/products/voyager-m-1.jpg",
            "https://images.example.com/products/voyager-m-2.jpg",
        ],
        "price": Decimal("4599.00"),
        "original_price": Decimal("4999.00"),
        "stock": 36,
        "sales": 21,
        "status": ProductStatus.ACTIVE,
        "is_featured": True,
        "detail": "经典三针自动机械款，兼顾通勤与正式场合佩戴需求。",
    },
    {
        "category_slug": "mechanical",
        "title": "Navigator Pro GMT",
        "subtitle": "双时区表盘设计",
        "cover_image": "https://images.example.com/products/navigator-pro-cover.jpg",
        "image_list": [
            "https://images.example.com/products/navigator-pro-1.jpg",
            "https://images.example.com/products/navigator-pro-2.jpg",
        ],
        "price": Decimal("6899.00"),
        "original_price": None,
        "stock": 18,
        "sales": 9,
        "status": ProductStatus.ACTIVE,
        "is_featured": False,
        "detail": "适合差旅和跨时区出行的 GMT 表款，兼具质感与功能性。",
    },
    {
        "category_slug": "accessories",
        "title": "Saffiano 真皮表带",
        "subtitle": "适配 20mm 通用表耳",
        "cover_image": "https://images.example.com/products/saffiano-strap-cover.jpg",
        "image_list": [
            "https://images.example.com/products/saffiano-strap-1.jpg",
            "https://images.example.com/products/saffiano-strap-2.jpg",
        ],
        "price": Decimal("299.00"),
        "original_price": Decimal("399.00"),
        "stock": 320,
        "sales": 207,
        "status": ProductStatus.ACTIVE,
        "is_featured": False,
        "detail": "快拆结构，适配多种表壳，适合作为表带替换与风格扩展。",
    },
    {
        "category_slug": "accessories",
        "title": "碳纤维旅行表盒",
        "subtitle": "双表位便携设计",
        "cover_image": "https://images.example.com/products/travel-case-cover.jpg",
        "image_list": [
            "https://images.example.com/products/travel-case-1.jpg",
            "https://images.example.com/products/travel-case-2.jpg",
        ],
        "price": Decimal("699.00"),
        "original_price": Decimal("899.00"),
        "stock": 48,
        "sales": 14,
        "status": ProductStatus.DRAFT,
        "is_featured": False,
        "detail": "用于演示草稿商品不会出现在商品浏览接口中。",
    },
]


def seed_categories() -> dict[str, ProductCategory]:
    with SessionLocal() as session:
        categories: dict[str, ProductCategory] = {}

        for payload in CATEGORY_SEEDS:
            category = session.scalar(
                select(ProductCategory).where(ProductCategory.slug == payload["slug"])
            )

            if category is None:
                category = ProductCategory(**payload)
                session.add(category)
            else:
                for key, value in payload.items():
                    setattr(category, key, value)

            session.flush()
            categories[payload["slug"]] = category

        session.commit()
        return categories


def seed_products() -> None:
    seed_categories()

    with SessionLocal() as session:
        db_categories = {
            category.slug: category
            for category in session.scalars(select(ProductCategory)).all()
        }

        for payload in PRODUCT_SEEDS:
            category = db_categories[payload["category_slug"]]
            lookup_statement = select(Product).where(
                Product.category_id == category.id,
                Product.title == payload["title"],
            )
            product = session.scalar(lookup_statement)

            values = dict(payload)
            values.pop("category_slug")
            values["category_id"] = category.id

            if product is None:
                product = Product(**values)
                session.add(product)
            else:
                for key, value in values.items():
                    setattr(product, key, value)

        session.commit()


def main() -> None:
    seed_products()
    print("Seed data inserted or updated successfully.")


if __name__ == "__main__":
    main()
