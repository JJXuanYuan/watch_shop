from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.api.deps import get_current_admin
from app.core.media import save_image_upload
from app.schemas.upload import AdminImageUploadResponse

router = APIRouter(prefix="/admin/uploads", tags=["admin-uploads"])


@router.post("/images", response_model=AdminImageUploadResponse)
async def upload_admin_image(
    request: Request,
    image: UploadFile = File(...),
    _current_admin=Depends(get_current_admin),
) -> AdminImageUploadResponse:
    url, filename, file_size = await save_image_upload(image=image, request=request)
    return AdminImageUploadResponse(
        url=url,
        filename=filename,
        size=file_size,
        content_type=image.content_type or "application/octet-stream",
    )
