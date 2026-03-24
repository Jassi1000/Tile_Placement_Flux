import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Sharpening kernel
_SHARPEN_KERNEL = np.array(
    [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0],
    ],
    dtype=np.float32,
)


def sharpen_image(image_bytes: bytes) -> bytes:
    """Decode image bytes, apply kernel sharpening, and return encoded bytes.

    Steps:
    1. Decode raw bytes into a NumPy array via cv2.imdecode.
    2. Apply a 3x3 sharpening kernel using cv2.filter2D.
    3. Encode the result back to JPEG bytes.
    """
    logger.info("Applying OpenCV sharpening to image (%d bytes)", len(image_bytes))

    # Decode
    nparr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes with OpenCV")

    # Sharpen
    sharpened = cv2.filter2D(img, ddepth=-1, kernel=_SHARPEN_KERNEL)

    # Re-encode
    success, buffer = cv2.imencode(".jpg", sharpened)
    if not success:
        raise RuntimeError("cv2.imencode failed to encode sharpened image")

    result_bytes: bytes = buffer.tobytes()
    logger.info("Sharpening complete; output size: %d bytes", len(result_bytes))
    return result_bytes
