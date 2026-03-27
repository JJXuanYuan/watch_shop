from enum import Enum


class AdminStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class CategoryStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ON_SALE = "on_sale"
    OFF_SALE = "off_sale"


class ProductDeletedFilter(str, Enum):
    NOT_DELETED = "not_deleted"
    DELETED = "deleted"
    ALL = "all"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"


class FulfillmentStatus(str, Enum):
    UNFULFILLED = "unfulfilled"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    COMPLETED = "completed"


class LogisticsCompanyStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
