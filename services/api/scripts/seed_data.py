from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.core.admin_auth import hash_admin_password
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import (
    AdminStatus,
    AdminUser,
    CategoryStatus,
    LogisticsCompany,
    LogisticsCompanyStatus,
    Product,
    ProductCategory,
    ProductStatus,
)

settings = get_settings()

CATEGORY_SEEDS = [
    {
        "name": "智能腕表",
        "slug": "smartwatch",
        "sort_order": 1,
        "status": CategoryStatus.ENABLED,
    },
    {
        "name": "机械腕表",
        "slug": "mechanical",
        "sort_order": 2,
        "status": CategoryStatus.ENABLED,
    },
    {
        "name": "表带配件",
        "slug": "accessories",
        "sort_order": 3,
        "status": CategoryStatus.ENABLED,
    },
]

PRODUCT_SEEDS = [
    {
        "category_slug": "smartwatch",
        "name": "Chronos S1 智能腕表",
        "subtitle": "全天候心率监测与双频 GPS",
        "cover_image": "https://images.example.com/products/chronos-s1-cover.jpg",
        "banner_images": [
            "https://images.example.com/products/chronos-s1-1.jpg",
            "https://images.example.com/products/chronos-s1-2.jpg",
        ],
        "price": Decimal("1999.00"),
        "original_price": Decimal("2299.00"),
        "stock": 120,
        "sales": 58,
        "status": ProductStatus.ON_SALE,
        "is_featured": True,
        "detail_content": "旗舰级智能腕表，支持运动记录、睡眠分析和 NFC 便捷支付。",
        "sort_order": 1,
    },
    {
        "category_slug": "smartwatch",
        "name": "Pulse Mini 轻量智能表",
        "subtitle": "轻薄机身，适合日常通勤佩戴",
        "cover_image": "https://images.example.com/products/pulse-mini-cover.jpg",
        "banner_images": [
            "https://images.example.com/products/pulse-mini-1.jpg",
            "https://images.example.com/products/pulse-mini-2.jpg",
        ],
        "price": Decimal("999.00"),
        "original_price": Decimal("1299.00"),
        "stock": 240,
        "sales": 132,
        "status": ProductStatus.ON_SALE,
        "is_featured": False,
        "detail_content": "主打轻盈与长续航，适合日常健康监测和基础运动记录。",
        "sort_order": 2,
    },
    {
        "category_slug": "mechanical",
        "name": "Voyager M 自动机械表",
        "subtitle": "蓝宝石镜面与 80 小时动储",
        "cover_image": "https://images.example.com/products/voyager-m-cover.jpg",
        "banner_images": [
            "https://images.example.com/products/voyager-m-1.jpg",
            "https://images.example.com/products/voyager-m-2.jpg",
        ],
        "price": Decimal("4599.00"),
        "original_price": Decimal("4999.00"),
        "stock": 36,
        "sales": 21,
        "status": ProductStatus.ON_SALE,
        "is_featured": True,
        "detail_content": "经典三针自动机械款，兼顾通勤与正式场合佩戴需求。",
        "sort_order": 1,
    },
    {
        "category_slug": "mechanical",
        "name": "Navigator Pro GMT",
        "subtitle": "双时区表盘设计",
        "cover_image": "https://images.example.com/products/navigator-pro-cover.jpg",
        "banner_images": [
            "https://images.example.com/products/navigator-pro-1.jpg",
            "https://images.example.com/products/navigator-pro-2.jpg",
        ],
        "price": Decimal("6899.00"),
        "original_price": None,
        "stock": 18,
        "sales": 9,
        "status": ProductStatus.ON_SALE,
        "is_featured": False,
        "detail_content": "适合差旅和跨时区出行的 GMT 表款，兼具质感与功能性。",
        "sort_order": 2,
    },
    {
        "category_slug": "accessories",
        "name": "Saffiano 真皮表带",
        "subtitle": "适配 20mm 通用表耳",
        "cover_image": "https://images.example.com/products/saffiano-strap-cover.jpg",
        "banner_images": [
            "https://images.example.com/products/saffiano-strap-1.jpg",
            "https://images.example.com/products/saffiano-strap-2.jpg",
        ],
        "price": Decimal("299.00"),
        "original_price": Decimal("399.00"),
        "stock": 320,
        "sales": 207,
        "status": ProductStatus.ON_SALE,
        "is_featured": False,
        "detail_content": "快拆结构，适配多种表壳，适合作为表带替换与风格扩展。",
        "sort_order": 1,
    },
    {
        "category_slug": "accessories",
        "name": "碳纤维旅行表盒",
        "subtitle": "双表位便携设计",
        "cover_image": "https://images.example.com/products/travel-case-cover.jpg",
        "banner_images": [
            "https://images.example.com/products/travel-case-1.jpg",
            "https://images.example.com/products/travel-case-2.jpg",
        ],
        "price": Decimal("699.00"),
        "original_price": Decimal("899.00"),
        "stock": 48,
        "sales": 14,
        "status": ProductStatus.DRAFT,
        "is_featured": False,
        "detail_content": "用于演示草稿商品不会出现在商品浏览接口中。",
        "sort_order": 99,
    },
]

LOGISTICS_COMPANY_SEEDS = [
    {"code": "SF", "name": "顺丰速运", "sort_order": 10, "status": LogisticsCompanyStatus.ENABLED},
    {"code": "YTO", "name": "圆通速递", "sort_order": 20, "status": LogisticsCompanyStatus.ENABLED},
    {"code": "ZTO", "name": "中通快递", "sort_order": 30, "status": LogisticsCompanyStatus.ENABLED},
    {"code": "STO", "name": "申通快递", "sort_order": 40, "status": LogisticsCompanyStatus.ENABLED},
    {"code": "YD", "name": "韵达速递", "sort_order": 50, "status": LogisticsCompanyStatus.ENABLED},
    {"code": "JT", "name": "极兔速递", "sort_order": 60, "status": LogisticsCompanyStatus.ENABLED},
    {"code": "EMS", "name": "中国邮政 EMS", "sort_order": 70, "status": LogisticsCompanyStatus.ENABLED},
]


def seed_admin_users() -> None:
    if settings.app_env.lower() == "production":
        print("Skip default admin seed in production environment.")
        return

    with SessionLocal() as session:
        admin_user = session.scalar(
            select(AdminUser).where(AdminUser.username == settings.admin_username)
        )

        if admin_user is None:
            admin_user = AdminUser(
                username=settings.admin_username,
                password_hash=hash_admin_password(settings.admin_password),
                status=AdminStatus.ACTIVE,
            )
            session.add(admin_user)
            session.commit()
            print(
                "Default admin user created for development. "
                "Change the password before using outside local development."
            )


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
                Product.name == payload["name"],
            )
            product = session.scalar(lookup_statement)

            values = dict(payload)
            values.pop("category_slug")
            values["category_id"] = category.id
            values["deleted_at"] = None

            if product is None:
                product = Product(**values)
                session.add(product)
            else:
                for key, value in values.items():
                    setattr(product, key, value)

        session.commit()


def seed_logistics_companies() -> None:
    with SessionLocal() as session:
        for payload in LOGISTICS_COMPANY_SEEDS:
            company = session.scalar(
                select(LogisticsCompany).where(LogisticsCompany.code == payload["code"])
            )

            if company is None:
                company = LogisticsCompany(**payload)
                session.add(company)
            else:
                for key, value in payload.items():
                    setattr(company, key, value)

        session.commit()


def main() -> None:
    seed_admin_users()
    seed_logistics_companies()
    seed_products()
    print("Seed data inserted or updated successfully.")


if __name__ == "__main__":
    main()
