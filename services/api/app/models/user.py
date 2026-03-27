from sqlalchemy import Enum, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.types import UserStatus


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_status_created_at", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    unionid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            name="user_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=text("'active'"),
    )

    cart_items = relationship("CartItem", back_populates="user")
    addresses = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders = relationship("Order", back_populates="user")
