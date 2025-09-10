from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.config_utils import EnvironmentType


class Settings(BaseSettings):
    PROJECT_NAME: str = "MCP Server"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.0.1"

    DEBUG: bool = False
    ENVIRONMENT: EnvironmentType = EnvironmentType.TEST

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    BACKEND_CORS_ALLOW_ALL: bool = False

    LOGGING_CONF_FILE: str = "logging.conf"

    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_USER: str = "elastic"
    ES_PASSWORD: SecretStr = SecretStr("elastic")
    ES_INDEX: str = "apple_health_data"

    CH_DIRNAME: str = "applehealth.chdb"
    CH_DB_NAME: str = "applehealth"
    CH_TABLE_NAME: str = "data"

    DUCKDB_FILENAME: str = "applehealth"

    CHUNK_SIZE: int = 50_000

    RAW_XML_PATH: str = "raw.xml"
    XML_SAMPLE_SIZE: int = 1000

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(Path(__file__).parent.parent / "config" / ".env"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg


settings = get_settings()
