from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    openai_api_key: str = Field(
        validation_alias=AliasChoices("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY")
    )

    openai_model: str = Field(
        validation_alias=AliasChoices("OPENAI_MODEL", "AZURE_OPENAI_MODEL")
    )

    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_BASE_URL",
            "OPENAI_BASE_URL",
        ),
    )

    openai_temperature: str | None = Field(default=None)

    @property
    def openai_temperature_float(self) -> float | None:
        """Get temperature as float, handling empty strings"""
        if self.openai_temperature is None or self.openai_temperature == '':
            return None
        try:
            return float(self.openai_temperature)
        except ValueError:
            return None


    @property
    def resolved_base_url(self) -> str | None:
        """
        If openai_base_url looks like a bare Azure endpoint, append /openai/v1/.
        If it's already a v1 URL, just normalise the trailing slash.
        """
        # Also check environment directly as fallback
        import os
        base_url = self.openai_base_url or os.getenv("AZURE_OPENAI_BASE_URL") or os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("OPENAI_BASE_URL")
        if not base_url:
            return None
        base = base_url.rstrip("/")
        if base.endswith("/openai/v1"):
            return base + "/"
        # Treat value as endpoint root and append v1 path
        return base + "/openai/v1/"


settings = Settings()
