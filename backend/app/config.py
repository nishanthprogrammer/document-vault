from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://vault:vault@localhost:5432/vault"
    redis_url: str = "redis://localhost:6379/0"
    s3_endpoint: str | None = "http://localhost:9000"
    s3_public_endpoint: str | None = None
    s3_bucket: str = "documents"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 15
    cors_origins: str = "http://localhost:3000"
    max_upload_size_bytes: int = 50 * 1024 * 1024
    upload_rate_limit: int = 10
    upload_rate_window_seconds: int = 60
    presigned_url_expires_seconds: int = 300
    aws_region: str = "ap-south-2"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

 
@lru_cache
def get_settings() -> Settings:
    return Settings()
