import io
import logging

import cloudinary.uploader

logger = logging.getLogger(__name__)


def upload_image_to_cloudinary(file) -> str:
    """Upload a file-like object to Cloudinary and return its secure URL."""
    logger.info("Uploading image to Cloudinary")
    result = cloudinary.uploader.upload(file)
    secure_url: str = result["secure_url"]
    logger.info("Image uploaded to Cloudinary: %s", secure_url)
    return secure_url


def upload_bytes_to_cloudinary(data: bytes) -> str:
    """Upload raw bytes to Cloudinary and return the secure URL."""
    logger.info("Uploading bytes to Cloudinary")
    result = cloudinary.uploader.upload(io.BytesIO(data))
    secure_url: str = result["secure_url"]
    logger.info("Bytes uploaded to Cloudinary: %s", secure_url)
    return secure_url
