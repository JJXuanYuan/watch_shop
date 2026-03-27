from sqlalchemy import Enum, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.types import LogisticsCompanyStatus


class LogisticsCompany(TimestampMixin, Base):
    __tablename__ = "logistics_companies"
    __table_args__ = (
        Index("ix_logistics_companies_status_sort_order", "status", "sort_order"),
        Index("ix_logistics_companies_status_name", "status", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    status: Mapped[LogisticsCompanyStatus] = mapped_column(
        Enum(
            LogisticsCompanyStatus,
            name="logistics_company_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=LogisticsCompanyStatus.ENABLED,
        server_default=text("'enabled'"),
    )
