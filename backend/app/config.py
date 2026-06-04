from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR}/data/influencers.db"
    thumbnails_dir: str = str(BASE_DIR / "data" / "thumbnails")

    ig_username: str = ""
    ig_password: str = ""
    ig_min_delay: float = 8.0
    ig_max_delay: float = 15.0

    tt_page_wait: float = 12.0
    posts_per_profile: int = 30

    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    class Config:
        env_file = str(BASE_DIR / ".env")
        case_sensitive = False


settings = Settings()
