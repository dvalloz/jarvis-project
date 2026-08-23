from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_user_id: int = Field(..., validation_alias="TELEGRAM_USER_ID")
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    groq_api_key: str = Field("gsk_placeholder_key", validation_alias="GROQ_API_KEY")
    openai_api_key: str = Field("sk_placeholder_key", validation_alias="OPENAI_API_KEY")
    timezone: str = Field("Europe/Madrid", validation_alias="TIMEZONE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
