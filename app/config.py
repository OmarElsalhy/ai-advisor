from pathlib import Path
import os
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent          
AI_ADVISOR_DIR = APP_DIR.parent                    
PROJECT_ROOT = AI_ADVISOR_DIR.parent               

load_dotenv(AI_ADVISOR_DIR / ".env")

STORAGE_DIR = Path(os.getenv("SHOPSPACE_STORAGE_DIR", str(AI_ADVISOR_DIR / "storage")))
CHROMA_DIR = STORAGE_DIR / "chroma"
DATABASE_PATH = STORAGE_DIR / "advisor.db"
KNOWLEDGE_ROOT = Path(os.getenv("SHOPSPACE_KNOWLEDGE_ROOT", str(PROJECT_ROOT)))
GENERAL_GUIDES_DIR = KNOWLEDGE_ROOT / "general_guides"
BUSINESS_GUIDES_DIR = KNOWLEDGE_ROOT / "business_guides"

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
APP_API_KEY = os.getenv("APP_API_KEY", "")
TOP_K = int(os.getenv("TOP_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Log configuration on startup
logger.debug(f"STORAGE_DIR: {STORAGE_DIR}")
logger.debug(f"KNOWLEDGE_ROOT: {KNOWLEDGE_ROOT}")
logger.debug(f"GENERAL_GUIDES_DIR: {GENERAL_GUIDES_DIR}")
logger.debug(f"BUSINESS_GUIDES_DIR: {BUSINESS_GUIDES_DIR}")
logger.info(f"Configuration loaded: TOP_K={TOP_K}, CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}")