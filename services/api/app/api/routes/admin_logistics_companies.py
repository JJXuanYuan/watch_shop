from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.models.logistics_company import LogisticsCompany
from app.models.types import LogisticsCompanyStatus
from app.schemas.logistics_company import (
    LogisticsCompanyListResponse,
    LogisticsCompanyResponse,
)

router = APIRouter(
    prefix="/admin/logistics-companies",
    tags=["admin-logistics-companies"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=LogisticsCompanyListResponse, summary="List enabled admin logistics companies")
def list_admin_logistics_companies(
    db: Session = Depends(get_db),
) -> LogisticsCompanyListResponse:
    companies = db.scalars(
        select(LogisticsCompany)
        .where(LogisticsCompany.status == LogisticsCompanyStatus.ENABLED)
        .order_by(LogisticsCompany.sort_order.asc(), LogisticsCompany.id.asc())
    ).all()

    return LogisticsCompanyListResponse(
        items=[
            LogisticsCompanyResponse.model_validate(company)
            for company in companies
        ],
    )
