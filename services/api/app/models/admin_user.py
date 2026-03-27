from sqlalchemy import Enum, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.types import AdminStatus


class AdminUser(TimestampMixin, Base):
    __tablename__ = "admin_users"
    __table_args__ = (
        Index("ix_admin_users_status_username", "status", "username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AdminStatus] = mapped_column(
        Enum(
            AdminStatus,
            name="admin_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=AdminStatus.ACTIVE,
        server_default=text("'active'"),
    )
