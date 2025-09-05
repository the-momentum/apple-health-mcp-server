from pathlib import Path
from functools import lru_cache

from pydantic import AnyHttpUrl, ValidationInfo, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.config_utils import EncryptedField, EnvironmentType


class Settings(BaseSettings):
    # FERNET_DECRYPTOR: FernetDecryptorField = Field("MASTER_KEY")

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

    CH_DB_NAME: str = "applehealth"
    CH_TABLE_NAME: str = "data"
    CHUNK_SIZE: int = 10_000

    RAW_XML_PATH: str = "raw.xml"
    XML_SAMPLE_SIZE: int = 1000

    @field_validator("*", mode="after")
    def _decryptor(cls, v, validation_info: ValidationInfo, *args, **kwargs):
        if isinstance(v, EncryptedField):
            return v.get_decrypted_value(validation_info.data["FERNET_DECRYPTOR"])
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(Path(__file__).parent.parent / "config" / ".env"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
