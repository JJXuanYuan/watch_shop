from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, Request, UploadFile, status

from app.core.config import Settings, get_settings

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpg": ".jpg",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


def ensure_media_directories(settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    active_settings.resolved_media_root.mkdir(parents=True, exist_ok=True)
    (active_settings.resolved_media_root / "uploads" / "images").mkdir(
        parents=True,
        exist_ok=True,
    )


def build_media_url(request: Request, relative_path: str, settings: Settings | None = None) -> str:
    active_settings = settings or get_settings()
    normalized_relative_path = relative_path.lstrip("/")
    base_url = active_settings.resolved_media_base_url
    if base_url is None:
        base_url = str(request.base_url).rstrip("/")
    return (
        f"{base_url}{active_settings.normalized_media_url_prefix}/{normalized_relative_path}"
    )


def resolve_image_extension(image: UploadFile) -> str:
    extension = Path(image.filename or "").suffix.lower()
    content_type = (image.content_type or "").lower()

    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only jpg, jpeg, png, and webp images are supported",
        )

    if extension and extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only jpg, jpeg, png, and webp images are supported",
        )

    return ALLOWED_IMAGE_CONTENT_TYPES[content_type]


async def save_image_upload(
    image: UploadFile,
    request: Request,
    settings: Settings | None = None,
) -> tuple[str, str, int]:
    active_settings = settings or get_settings()
    ensure_media_directories(active_settings)

    extension = resolve_image_extension(image)
    relative_directory = Path("uploads") / "images" / datetime.now(UTC).strftime("%Y/%m")
    target_directory = active_settings.resolved_media_root / relative_directory
    target_directory.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now(UTC):%Y%m%d%H%M%S}_{uuid4().hex}{extension}"
    target_path = target_directory / filename
    file_size = 0

    try:
        with target_path.open("wb") as output_file:
            while True:
                chunk = await image.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break

                file_size += len(chunk)
                if file_size > active_settings.media_image_max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            "Image file is too large. "
                            f"Maximum size is {active_settings.media_image_max_bytes} bytes"
                        ),
                    )

                output_file.write(chunk)
    except Exception:
        if target_path.exists():
            target_path.unlink()
        raise
    finally:
        await image.close()

    relative_path = (relative_directory / filename).as_posix()
    return build_media_url(request, relative_path, active_settings), filename, file_size
