from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.types import LogisticsCompanyStatus


class LogisticsCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    sort_order: int
    status: LogisticsCompanyStatus
    created_at: datetime
    updated_at: datetime


class LogisticsCompanyListResponse(BaseModel):
    items: list[LogisticsCompanyResponse]
