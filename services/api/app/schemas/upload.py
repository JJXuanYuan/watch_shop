from pydantic import BaseModel


class AdminImageUploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
