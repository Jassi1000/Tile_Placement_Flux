import base64
import logging
import os

import requests

from services.cloudinary_service import upload_bytes_to_cloudinary

logger = logging.getLogger(__name__)

AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_ENDPOINT = os.getenv("AI_ENDPOINT", "https://api.example.com/generate")

PROMPT_TEMPLATE = (
    "You are a professional architectural rendering AI.\n\n"
    "Improve the realism of the given interior image.\n\n"
    "The image already contains tiles placed on surfaces. "
    "Your job is to enhance it to look like a real photograph.\n\n"
    "Enhancement level: {enhancement_level}\n\n"
    "Rules:\n"
    "* Improve lighting consistency and shadows\n"
    "* Fix perspective alignment if slightly incorrect\n"
    "* Enhance texture sharpness and clarity\n"
    "* Ensure tiles blend naturally with the surface\n"
    "* Add realistic reflections if applicable\n"
    "* Preserve all objects and layout\n"
    "* Do NOT change structure or move objects\n"
    "* Do NOT add new elements\n"
    "* Output must look photorealistic\n\n"
    "If the image is already realistic, return it unchanged.\n\n"
    "Return only the final enhanced image."
)


def call_ai_model(image_url: str, enhancement_level: str) -> str:
    """Call the AI enhancement API and return the URL of the resulting image.

    The function handles both response formats:
      - {"image_url": "https://..."}
      - {"image_base64": "<base64 string>"}
    """
    prompt = PROMPT_TEMPLATE.format(enhancement_level=enhancement_level)
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "image_url": image_url,
        "prompt": prompt,
        "enhancement_level": enhancement_level,
    }

    logger.info(
        "Calling AI model at %s with enhancement_level=%s",
        AI_ENDPOINT,
        enhancement_level,
    )

    response = requests.post(AI_ENDPOINT, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data: dict = response.json()

    # Case 1 – API returns a direct URL
    if "image_url" in data:
        result_url: str = data["image_url"]
        logger.info("AI model returned URL: %s", result_url)
        return result_url

    # Case 2 – API returns a base64-encoded image
    if "image_base64" in data:
        logger.info("AI model returned base64 image; re-uploading to Cloudinary")
        image_bytes = base64.b64decode(data["image_base64"])
        result_url = upload_bytes_to_cloudinary(image_bytes)
        return result_url

    raise ValueError(f"Unexpected AI API response format: {list(data.keys())}")
