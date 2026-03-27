from sqlalchemy import Enum, Index, Integer, String, text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.types import CategoryStatus


class ProductCategory(TimestampMixin, Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        Index("ix_product_categories_status_sort_order", "status", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    status: Mapped[CategoryStatus] = mapped_column(
        Enum(
            CategoryStatus,
            name="category_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=CategoryStatus.ENABLED,
        server_default=text("'enabled'"),
    )

    products = relationship("Product", back_populates="category")

    @hybrid_property
    def is_active(self) -> bool:
        return self.status == CategoryStatus.ENABLED

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.status = (
            CategoryStatus.ENABLED if value else CategoryStatus.DISABLED
        )

    @is_active.expression
    def is_active(cls):  # type: ignore[no-redef]
        return cls.status == CategoryStatus.ENABLED
