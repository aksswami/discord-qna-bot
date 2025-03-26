"""OAuth server for handling Discord authentication."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from src.api.discord_client import DiscordClient
from src.auth.token_manager import TokenManager
from src.config.settings import ServerConfig, settings
from src.core.dependencies import get_discord_client
from src.models.token_models import TokenModel

app = FastAPI(title="Discord OAuth Server")
app.dependency_overrides[get_discord_client] = lambda: get_discord_client(
    settings.discord
)

# Initialize token storage
token_manager = TokenManager()


@app.get("/")
async def root() -> Dict[str, str]:
    """Return a status message indicating the server is running."""
    return {"message": "Discord OAuth Server is running"}


@app.get("/auth", dependencies=[Depends(get_discord_client)])
async def auth() -> RedirectResponse:
    """Redirect to Discord OAuth authorization page."""
    discord_client = get_discord_client(settings.discord)
    auth_url = discord_client.get_authorization_url(
        scopes=["identify", "guilds", "messages.read"]
    )
    return RedirectResponse(url=auth_url)


@app.get("/oauth2/callback")
async def callback(code: str, state: Optional[str] = None) -> Dict[str, str|int]:
    """Handle the OAuth callback from Discord."""
    try:
        print(f"Received code from callback: {code}")
        # Exchange the code for a token
        token_response = await DiscordClient.exchange_code_for_token(
            code, config=settings.discord
        )
        token_data = TokenModel(
            access_token=token_response.access_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            refresh_token=token_response.refresh_token,
            scope=token_response.scope,
            expires_at=datetime.utcnow() + timedelta(seconds=token_response.expires_in),
        )

        # Save the token
        token_id = str(len(token_manager._tokens) + 1)
        token_manager.save_token(token_id, token_data)

        # Redirect to a success page or your main application
        return {
            "message": "Authentication successful",
            "token_id": token_id,
            "access_token": token_response.access_token,
            "token_type": token_response.token_type,
            "expires_in": token_response.expires_in,
            "refresh_token": token_response.refresh_token,
            "scope": token_response.scope,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error during OAuth flow: {str(e)}"
        )