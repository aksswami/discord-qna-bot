"""Application dependencies for dependency injection."""

from src.api.discord_client import DiscordClient
from src.config.settings import DiscordConfig


def get_discord_client(discord_config: DiscordConfig) -> DiscordClient:
    """Factory function for creating Discord client instances."""
    return DiscordClient(discord_config)
