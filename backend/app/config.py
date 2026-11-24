from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8-sig", extra="ignore")

    keitaro_api_url: str = "https://keitaro-for-tests.etolegko.com/admin_api/v1"
    keitaro_api_key: str = ""
    keitaro_admin_url: str = "https://keitaro-for-tests.etolegko.com/admin/#!/campaign.editor/"
    keitaro_timeout: float = 30.0

    default_domain_id: int = 1813
    default_group_id: int = 10332
    default_traffic_source_id: int = 836
    geo_redirect_url: str = "https://google.com"

    database_url: str = f"sqlite:///{(BASE_DIR / 'keitaro.db').as_posix()}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
