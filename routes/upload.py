import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.cloudinary_service import upload_image_to_cloudinary

logger = logging.getLogger(__name__)

router = APIRouter()


class UploadResponse(BaseModel):
    image_url: str


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Receive an uploaded image and store it on Cloudinary.

    Returns the Cloudinary secure URL.
    """
    logger.info("Received upload request for file: %s", file.filename)
    try:
        secure_url = upload_image_to_cloudinary(file.file)
    except Exception as exc:
        logger.exception("Cloudinary upload failed")
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {exc}") from exc

    return UploadResponse(image_url=secure_url)
