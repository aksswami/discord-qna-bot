from src.client.discord_api import DiscordAPI

from .config import DiscordConfig


def discord_client(discord_config: DiscordConfig) -> DiscordAPI:
    return DiscordAPI(discord_config);
   
