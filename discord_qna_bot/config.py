from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file"""
    
    # Discord OAuth settings
    discord_client_id: str = Field(..., description="Discord OAuth client ID")
    discord_client_secret: str = Field(..., description="Discord OAuth client secret")
    discord_redirect_uri: str = Field(..., description="Discord OAuth redirect URI")
    
    # Discord Bot settings
    discord_bot_token: Optional[str] = Field(None, description="Discord bot token")
    
    # Server settings
    host: str = Field("0.0.0.0", description="Host to bind the server to")
    port: int = Field(8000, description="Port to bind the server to")
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Create a global instance of the settings
settings = Settings()
