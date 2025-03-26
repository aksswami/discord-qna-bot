from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DiscordConfig(BaseModel):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    bot_token: Optional[str] = None


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file"""

    discord: DiscordConfig = DiscordConfig()
    server: ServerConfig = ServerConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        env_prefix="APP_",
    )


# Create a global instance of the settings
settings = Settings()
