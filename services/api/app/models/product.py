from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.types import ProductStatus


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category_id_status", "category_id", "status"),
        Index("ix_products_deleted_at_status", "deleted_at", "status"),
        Index("ix_products_status_is_featured", "status", "is_featured"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("product_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column("title", String(255), nullable=False, index=True)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cover_image: Mapped[str] = mapped_column(String(500), nullable=False)
    banner_images: Mapped[list[str]] = mapped_column(
        "image_list",
        JSON,
        nullable=False,
        default=list,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    sales: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    status: Mapped[ProductStatus] = mapped_column(
        Enum(
            ProductStatus,
            name="product_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=ProductStatus.DRAFT,
        server_default=text("'draft'"),
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    detail_content: Mapped[Optional[str]] = mapped_column("detail", Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(),
        nullable=True,
    )

    category = relationship("ProductCategory", back_populates="products")

    @property
    def title(self) -> str:
        return self.name

    @title.setter
    def title(self, value: str) -> None:
        self.name = value

    @property
    def image_list(self) -> list[str]:
        return self.banner_images

    @image_list.setter
    def image_list(self, value: list[str]) -> None:
        self.banner_images = value

    @property
    def detail(self) -> Optional[str]:
        return self.detail_content

    @detail.setter
    def detail(self, value: Optional[str]) -> None:
        self.detail_content = value

    @hybrid_property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @is_deleted.expression
    def is_deleted(cls):  # type: ignore[no-redef]
        return cls.deleted_at.is_not(None)
