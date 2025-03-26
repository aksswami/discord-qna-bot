"""Discord service for handling higher-level Discord operations."""

from typing import List, Optional

from src.api.discord_client import DiscordClient
from src.auth.token_manager import TokenManager
from src.config.settings import settings
from src.models.discord_models import GuildModel, MessageModel, TokenType


class DiscordService:
    """Service for Discord operations."""

    def __init__(
        self, token: Optional[str] = None, token_type: TokenType = TokenType.BOT
    ):
        """Initialize Discord service with optional token."""
        self.token_manager = TokenManager()

        if token:
            self.client = DiscordClient(token=token, token_type=token_type)
        else:
            # Try to get token from token manager
            token_model = self.token_manager.get_latest_token()
            if token_model and not token_model.is_expired():
                self.client = DiscordClient(
                    token=token_model.access_token, token_type=TokenType.USER
                )
            else:
                # Fall back to bot token from settings
                self.client = DiscordClient(
                    config=settings.discord,
                    token=settings.discord.bot_token,
                    token_type=TokenType.BOT,
                )

    async def close(self) -> None:
        """Close the Discord client."""
        await self.client.close()

    async def authenticate_user(self) -> bool:
        """Authenticate the user using the OAuth flow."""
        token_model = self.token_manager.get_latest_token()
        if token_model and not token_model.is_expired():
            self.client = DiscordClient(
                token=token_model.access_token, token_type=TokenType.USER
            )
            return True
        return False

    async def get_all_guilds(self) -> List[GuildModel]:
        """Get all guilds for the current user."""
        return await self.client.get_current_user_guilds()

    async def fetch_messages_from_guild(
        self, guild_id: str, limit: int = 50
    ) -> List[MessageModel]:
        """Fetch messages from all channels in a guild."""
        channels = await self.client.get_guild_channels(guild_id)
        text_channels = [channel for channel in channels if channel.type == 0]

        all_messages = []
        for channel in text_channels:
            try:
                messages = await self.client.get_channel_messages(
                    channel.id, limit=limit
                )
                all_messages.extend(messages)
            except Exception as e:
                print(f"Error fetching messages from channel {channel.name}: {e}")

        return all_messages

    async def fetch_messages_from_all_guilds(
        self, limit_per_channel: int = 50
    ) -> List[MessageModel]:
        """Fetch messages from all guilds and channels the user has access to."""
        guilds = await self.get_all_guilds()
        all_messages = []

        for guild in guilds:
            guild_messages = await self.fetch_messages_from_guild(
                guild.id, limit=limit_per_channel
            )
            all_messages.extend(guild_messages)

        return all_messages
