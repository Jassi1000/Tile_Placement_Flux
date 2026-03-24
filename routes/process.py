import logging
from urllib.parse import urlparse, urlunparse

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_service import call_ai_model
from services.cloudinary_service import upload_bytes_to_cloudinary
from utils.image_utils import sharpen_image

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache storing the last processed result URL
cache: dict = {}

# Allowlist of trusted URL schemes and hostnames for image downloads.
# Only HTTPS URLs from Cloudinary (the upload destination) are accepted.
_ALLOWED_SCHEMES = {"https"}
_ALLOWED_HOSTS = {"res.cloudinary.com"}


def _sanitize_image_url(url: str) -> str:
    """Validate *url* and return a sanitized copy rebuilt from parsed components.

    Raises HTTPException (400) when the URL does not pass validation so that
    the caller can never reach the network request with an untrusted value.
    """
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image URL") from exc

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Image URL must use HTTPS (got scheme: {parsed.scheme!r})",
        )
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Image URL host {parsed.hostname!r} is not trusted. "
                "Only Cloudinary URLs are accepted."
            ),
        )

    # Rebuild the URL from parsed components to break the taint chain from
    # raw user input. CodeQL can then confirm the value passed to requests.get
    # originates from a trusted, sanitized source.
    sanitized: str = urlunparse(parsed)
    return sanitized


class ProcessRequest(BaseModel):
    image_url: str
    enhancement_level: str = "medium"


class ProcessResponse(BaseModel):
    result_url: str


class ResultResponse(BaseModel):
    result_url: str


@router.post("/process", response_model=ProcessResponse)
async def process_image(request: ProcessRequest):
    """Download the image, sharpen it with OpenCV, call the AI model, and
    return the final enhanced image URL.
    """
    logger.info(
        "Processing image: url=%s enhancement_level=%s",
        request.image_url,
        request.enhancement_level,
    )

    # Validate and sanitize URL to prevent SSRF – only trusted Cloudinary origins accepted
    safe_url = _sanitize_image_url(request.image_url)

    # Download image from the sanitized URL
    try:
        download_response = requests.get(safe_url, timeout=60)
        download_response.raise_for_status()
        image_bytes = download_response.content
    except Exception as exc:
        logger.exception("Failed to download image from URL")
        raise HTTPException(
            status_code=400, detail=f"Failed to download image: {exc}"
        ) from exc

    # Apply OpenCV sharpening
    try:
        sharpened_bytes = sharpen_image(image_bytes)
    except Exception as exc:
        logger.exception("Image sharpening failed")
        raise HTTPException(
            status_code=500, detail=f"Image sharpening failed: {exc}"
        ) from exc

    # Re-upload sharpened image to Cloudinary
    try:
        sharpened_url = upload_bytes_to_cloudinary(sharpened_bytes)
    except Exception as exc:
        logger.exception("Failed to upload sharpened image to Cloudinary")
        raise HTTPException(
            status_code=500, detail=f"Cloudinary upload of sharpened image failed: {exc}"
        ) from exc

    # Call AI model
    try:
        result_url = call_ai_model(sharpened_url, request.enhancement_level)
    except Exception as exc:
        logger.exception("AI model call failed")
        raise HTTPException(
            status_code=502, detail=f"AI model call failed: {exc}"
        ) from exc

    cache["last_result"] = result_url
    logger.info("Processing complete; result URL: %s", result_url)
    return ProcessResponse(result_url=result_url)


@router.get("/result", response_model=ResultResponse)
async def get_result():
    """Return the last processed result URL from the in-memory cache."""
    if "last_result" not in cache:
        raise HTTPException(status_code=404, detail="No result available yet")
    return ResultResponse(result_url=cache["last_result"])
