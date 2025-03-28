"""Token manager for Discord OAuth tokens."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.token_models import TokenModel


class TokenManager:
    """Class for managing Discord OAuth tokens."""

    def __init__(self, storage_path: str = "~/.discord_qna_bot/tokens.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._tokens: dict[str, TokenModel] = {}
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from storage file."""
        if self.storage_path.exists():
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for token_id, token_data in data.items():
                    token_data["created_at"] = datetime.fromisoformat(
                        token_data["created_at"]
                    )
                    if token_data.get("expires_at"):
                        token_data["expires_at"] = datetime.fromisoformat(
                            token_data["expires_at"]
                        )
                    self._tokens[token_id] = TokenModel(**token_data)

    def _save_tokens(self) -> None:
        """Save tokens to storage file."""
        data = {}
        for token_id, token_data in self._tokens.items():
            data[token_id] = token_data.model_dump()
            data[token_id]["created_at"] = token_data.created_at.isoformat()
            if token_data.expires_at:
                data[token_id]["expires_at"] = token_data.expires_at.isoformat()

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def save_token(self, token_id: str, token_data: TokenModel) -> None:
        """Save a new token."""
        self._tokens[token_id] = token_data
        self._save_tokens()

    def get_token(self, token_id: str) -> Optional[TokenModel]:
        """Get a token by ID."""
        return self._tokens.get(token_id)

    def get_latest_token(self) -> Optional[TokenModel]:
        """Get the most recently created token."""
        if not self._tokens:
            return None
        return max(self._tokens.values(), key=lambda x: x.created_at)

    def delete_token(self, token_id: str) -> None:
        """Delete a token by ID."""
        if token_id in self._tokens:
            del self._tokens[token_id]
            self._save_tokens()
