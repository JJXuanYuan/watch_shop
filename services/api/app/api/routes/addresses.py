from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.address import Address
from app.models.user import User
from app.schemas.address import (
    AddressCreateRequest,
    AddressDefaultResponse,
    AddressListResponse,
    AddressResponse,
    AddressUpdateRequest,
    build_full_address,
)

router = APIRouter(prefix="/addresses", tags=["addresses"])


def _address_query(user_id: int):
    return (
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.updated_at.desc(), Address.id.desc())
    )


def _build_address_response(address: Address) -> AddressResponse:
    return AddressResponse(
        id=address.id,
        receiver_name=address.receiver_name,
        receiver_phone=address.receiver_phone,
        province=address.province,
        city=address.city,
        district=address.district,
        detail_address=address.detail_address,
        full_address=build_full_address(
            address.province,
            address.city,
            address.district,
            address.detail_address,
        ),
        is_default=address.is_default,
        created_at=address.created_at,
        updated_at=address.updated_at,
    )


def _get_address_or_404(address_id: int, user_id: int, db: Session) -> Address:
    address = db.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="地址不存在",
        )
    return address


def _clear_other_defaults(user_id: int, keep_id: int | None, db: Session) -> None:
    filters = [Address.user_id == user_id]
    if keep_id is not None:
        filters.append(Address.id != keep_id)

    db.execute(
        update(Address)
        .where(*filters)
        .values(is_default=False)
    )


def _ensure_default_address(user_id: int, db: Session, exclude_id: int | None = None) -> None:
    current_default = db.scalar(
        select(Address.id).where(Address.user_id == user_id, Address.is_default.is_(True))
    )
    if current_default is not None:
        return

    filters = [Address.user_id == user_id]
    if exclude_id is not None:
        filters.append(Address.id != exclude_id)

    candidate = db.scalar(
        select(Address)
        .where(*filters)
        .order_by(Address.updated_at.desc(), Address.id.desc())
        .limit(1)
    )
    if candidate is not None:
        candidate.is_default = True
        return

    if exclude_id is not None:
        fallback = db.scalar(
            select(Address).where(Address.id == exclude_id, Address.user_id == user_id)
        )
        if fallback is not None:
            fallback.is_default = True


@router.get("", response_model=AddressListResponse, summary="List current user addresses")
def list_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AddressListResponse:
    addresses = db.scalars(_address_query(current_user.id)).all()
    return AddressListResponse(
        items=[_build_address_response(address) for address in addresses]
    )


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create current user address",
)
def create_address(
    payload: AddressCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AddressResponse:
    has_existing_address = db.scalar(
        select(Address.id).where(Address.user_id == current_user.id).limit(1)
    )
    is_default = payload.is_default or has_existing_address is None

    address = Address(
        user_id=current_user.id,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        province=payload.province,
        city=payload.city,
        district=payload.district,
        detail_address=payload.detail_address,
        is_default=is_default,
    )
    db.add(address)
    db.flush()

    if is_default:
        _clear_other_defaults(current_user.id, address.id, db)

    db.commit()
    db.refresh(address)
    return _build_address_response(address)


@router.put(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Update current user address",
)
def update_address(
    payload: AddressUpdateRequest,
    address_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AddressResponse:
    address = _get_address_or_404(address_id, current_user.id, db)

    address.receiver_name = payload.receiver_name
    address.receiver_phone = payload.receiver_phone
    address.province = payload.province
    address.city = payload.city
    address.district = payload.district
    address.detail_address = payload.detail_address

    if payload.is_default:
        address.is_default = True
        _clear_other_defaults(current_user.id, address.id, db)
    elif address.is_default:
        address.is_default = False
        _ensure_default_address(current_user.id, db, exclude_id=address.id)

    _ensure_default_address(current_user.id, db)

    db.commit()
    db.refresh(address)
    return _build_address_response(address)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user address",
)
def delete_address(
    address_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    address = _get_address_or_404(address_id, current_user.id, db)
    was_default = address.is_default
    db.delete(address)
    db.flush()

    if was_default:
        _ensure_default_address(current_user.id, db)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{address_id}/default",
    response_model=AddressDefaultResponse,
    summary="Set current user default address",
)
@router.post(
    "/{address_id}/default",
    response_model=AddressDefaultResponse,
    summary="Set current user default address",
)
def set_default_address(
    address_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AddressDefaultResponse:
    address = _get_address_or_404(address_id, current_user.id, db)
    address.is_default = True
    _clear_other_defaults(current_user.id, address.id, db)
    db.commit()

    return AddressDefaultResponse(id=address.id, is_default=True)
