import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///local.db")
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "assets/images")
    AUDIO_FOLDER: str = os.getenv("AUDIO_FOLDER", "assets/audio")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")

os.makedirs(Settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Settings.AUDIO_FOLDER, exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(Settings.LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("CV_App")
