"""Discord API client for interacting with Discord's REST API."""

from typing import List, Optional

import httpx

from src.config.settings import DiscordConfig
from src.models.discord_models import (
    ChannelModel,
    GuildModel,
    MessageModel,
    OAuth2TokenResponse,
    TokenType,
)


class DiscordClient:
    """Client for interacting with Discord's REST API."""

    def __init__(
        self,
        config: Optional[DiscordConfig] = None,
        token: Optional[str] = None,
        token_type: TokenType = TokenType.BOT,
    ):
        self.api_base = "https://discord.com/api/v10"
        self.oauth_base = "https://discord.com/oauth2"
        self.client_id = config.client_id if config else None
        self.client_secret = config.client_secret if config else None
        self.redirect_uri = config.redirect_uri if config else None

        if token:
            self.headers = {
                "Authorization": f"{'Bot' if token_type == TokenType.BOT else 'Bearer'} {token}",
                "Content-Type": "application/json",
            }
        else:
            self.headers = {"Content-Type": "application/json"}

        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    @classmethod
    async def exchange_code_for_token(
        cls, code: str, config: DiscordConfig
    ) -> OAuth2TokenResponse:
        """Exchange authorization code for access token."""
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://discord.com/api/v10/oauth2/token", data=data
            )
            response.raise_for_status()
            return OAuth2TokenResponse(**response.json())

    def get_authorization_url(self, scopes: List[str]) -> str:
        """Generate authorization URL for OAuth2 flow."""
        scope_string = " ".join(scopes)
        return (
            f"{self.oauth_base}/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope={scope_string}"
        )

    async def close(self) -> None:
        """Close the HTTP client session."""
        await self.client.aclose()

    async def get_current_user_guilds(self) -> List[GuildModel]:
        """Get guilds (servers) for the current user."""
        response = await self.client.get(f"{self.api_base}/users/@me/guilds")
        response.raise_for_status()
        return [GuildModel(**guild) for guild in response.json()]

    async def create_guild(self, name: str, icon: Optional[str] = None) -> GuildModel:
        """Create a new guild (server)."""
        payload = {"name": name}
        if icon:
            payload["icon"] = icon

        response = await self.client.post(f"{self.api_base}/guilds", json=payload)
        response.raise_for_status()
        return GuildModel(**response.json())

    async def get_guild_channels(self, guild_id: str) -> List[ChannelModel]:
        """Get channels for a specific guild."""
        response = await self.client.get(f"{self.api_base}/guilds/{guild_id}/channels")
        response.raise_for_status()
        return [ChannelModel(**channel) for channel in response.json()]

    async def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None,
        around: Optional[str] = None,
    ) -> List[MessageModel]:
        """Get messages from a specific channel with pagination support."""
        params = {"limit": min(limit, 100)}  # Discord's max limit is 100

        # Only one of these parameters can be used at a time
        if before:
            params["before"] = before
        elif after:
            params["after"] = after
        elif around:
            params["around"] = around

        response = await self.client.get(
            f"{self.api_base}/channels/{channel_id}/messages", params=params
        )
        response.raise_for_status()
        return [MessageModel(**message) for message in response.json()]
