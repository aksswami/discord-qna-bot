"""Token models for Discord OAuth tokens."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenModel(BaseModel):
    """Model for storing Discord OAuth token data."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return True
        return datetime.utcnow() >= self.expires_at
