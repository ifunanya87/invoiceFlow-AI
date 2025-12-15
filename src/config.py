from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class BaseConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(ENV_FILE_PATH)),
        extra="ignore",
        frozen=True,
        env_nested_delimiter="__",
        case_sensitive=False,
    )


# Sub-configs
class DatabaseSettings(BaseConfigSettings):
    postgres_url: str = "postgresql://invoice_user:invoice_pass@localhost:5432/invoice_db"
    pool_size: int = 10
    max_overflow: int = 5
    echo_sql: bool = False

    @field_validator("postgres_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("postgresql://"):
            raise ValueError("Database URL must start with 'postgresql://'")
        return v

class OCRSettings(BaseConfigSettings):
    max_pages: int = 20
    ocr_output_mode: Literal["text", "json", "table"] = "text"


class LLMParserSettings(BaseConfigSettings):
    model_name: str = "gpt-4o-mini"
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    max_retries: int = 3
    retry_delay_sec: float = 2.0


# class AppSettings(BaseConfigSettings):
#     service_name: str = "InvoiceAI"
#     environment: Literal["development", "staging", "production"] = "development"
#     debug: bool = True


# Main Settings
class Settings(BaseConfigSettings):
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    llm: LLMParserSettings = Field(default_factory=LLMParserSettings)
    # app: AppSettings = Field(default_factory=AppSettings)

@lru_cache
def get_settings() -> Settings:
    return Settings()
