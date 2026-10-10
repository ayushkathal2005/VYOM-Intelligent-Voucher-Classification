"""Application configuration settings for VYOM+."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for backend environment."""

    # Server Settings
    environment: str = Field(default="development", description="Environment: development, test, production")
    host: str = Field(default="127.0.0.1", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")
    log_level: str = Field(default="info", description="Logging verbosity")

    # AI Model Settings
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    gemini_model: str = Field(default="gemma-4-26b-a4b-it", description="Designated Gemma 4 model identifier")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_gemini_configured(self) -> bool:
        """Return True if a valid Gemini API key is configured."""
        return bool(self.gemini_api_key and self.gemini_api_key.strip())


# Singleton instance
settings = Settings()
