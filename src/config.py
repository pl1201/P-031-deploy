from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI20K Agent"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # LLM
    openai_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # LLM — Gemini (nhiều key free để xoay vòng khi rate-limit)
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""
    gemini_api_key_5: str = ""
    # 2026-08-18: 2.5-flash bị Google khai tử cho tài khoản mới (404 NOT_FOUND,
    # "no longer available to new users") — xác minh trực tiếp qua API, không phải bug code.
    # 2.0-flash free-tier limit=0; 1.5 đã ngừng. Đã thử thật với key hiện tại: 3.5-flash chạy
    # được, 2.5-flash-lite CŨNG đã bị khai tử, "-latest" alias hay bị 503 quá tải dùng chung.
    gemini_model: str = "gemini-3.5-flash"

    # USDA FoodData Central (món nhập khẩu / vi chất NIN thiếu) — DAT-03
    usda_api_key: str = ""

    # Cách chọn món cho `generate_menu` (AGT-10):
    #   hybrid — CP-SAT ở lượt đầu, chuyển LLM khi vô nghiệm hoặc phải sửa theo feedback
    #   cpsat  — chỉ CP-SAT, không gọi LLM (tất định, không tốn token, không cần key)
    #   gemini — chỉ LLM (hành vi trước AGT-10)
    menu_generator: Literal["hybrid", "cpsat", "gemini"] = "hybrid"

    def gemini_keys(self) -> list[str]:
        """Danh sách key Gemini không rỗng, theo thứ tự ưu tiên xoay vòng."""
        keys = [
            self.gemini_api_key,
            self.gemini_api_key_2,
            self.gemini_api_key_3,
            self.gemini_api_key_4,
            self.gemini_api_key_5,
        ]
        return [k.strip() for k in keys if k and k.strip()]

    # Auth (BE-02)
    jwt_secret: str = "dev-only-insecure-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 7

    # Database
    database_url: str = "sqlite:///./data/app.db"
    db_connect_timeout_sec: int = Field(default=10, ge=1, le=60)
    db_pool_timeout_sec: int = Field(default=10, ge=1, le=60)
    db_pool_recycle_sec: int = Field(default=300, ge=30, le=3600)
    db_pool_size: int = Field(default=3, ge=1, le=20)
    db_max_overflow: int = Field(default=2, ge=0, le=20)

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
