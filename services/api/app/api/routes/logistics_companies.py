from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.logistics_company import LogisticsCompany
from app.models.types import LogisticsCompanyStatus
from app.schemas.logistics_company import (
    LogisticsCompanyListResponse,
    LogisticsCompanyResponse,
)

router = APIRouter(prefix="/logistics-companies", tags=["logistics-companies"])


def _query_enabled_logistics_companies(db: Session) -> list[LogisticsCompany]:
    return db.scalars(
        select(LogisticsCompany)
        .where(LogisticsCompany.status == LogisticsCompanyStatus.ENABLED)
        .order_by(LogisticsCompany.sort_order.asc(), LogisticsCompany.id.asc())
    ).all()


@router.get("", response_model=LogisticsCompanyListResponse, summary="List enabled logistics companies")
def list_logistics_companies(
    db: Session = Depends(get_db),
) -> LogisticsCompanyListResponse:
    return LogisticsCompanyListResponse(
        items=[
            LogisticsCompanyResponse.model_validate(company)
            for company in _query_enabled_logistics_companies(db)
        ],
    )
