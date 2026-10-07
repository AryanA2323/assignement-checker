import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load environment variables
load_dotenv(dotenv_path=ENV_FILE)

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    DEFAULT_STRICTNESS = os.getenv("DEFAULT_STRICTNESS", "standard").strip().lower()
    MANUAL_REVIEW_THRESHOLD = float(os.getenv("MANUAL_REVIEW_THRESHOLD", "70.0"))
    
    UPLOAD_DIR = BASE_DIR / "uploads"
    DEMO_DIR = BASE_DIR / "demo_data"
    REPORTS_DIR = BASE_DIR / "reports"
    
    # Supported image & document extensions
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    ALLOWED_DOC_EXTENSIONS = {".pdf", ".json", ".txt", ".md"}

    @classmethod
    def has_api_key(cls) -> bool:
        """Check if a Gemini API key is configured."""
        return bool(cls.GEMINI_API_KEY and len(cls.GEMINI_API_KEY) > 10)

    @classmethod
    def set_api_key(cls, key: str) -> None:
        """Update API key dynamically and persist to .env."""
        cls.GEMINI_API_KEY = key.strip()
        os.environ["GEMINI_API_KEY"] = cls.GEMINI_API_KEY
        
        # Read or create .env content
        lines = []
        key_found = False
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        lines.append(f"GEMINI_API_KEY={cls.GEMINI_API_KEY}\n")
                        key_found = True
                    else:
                        lines.append(line)
        if not key_found:
            lines.append(f"GEMINI_API_KEY={cls.GEMINI_API_KEY}\n")
            
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

# Ensure required directories exist
Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Config.DEMO_DIR.mkdir(parents=True, exist_ok=True)
Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
