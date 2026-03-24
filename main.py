import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import cloudinary

from routes.upload import router as upload_router
from routes.process import router as process_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

app = FastAPI(title="Tile Placement Flux", version="1.0.0")

app.include_router(upload_router)
app.include_router(process_router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

logger.info("Tile Placement Flux application started")
