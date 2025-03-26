#!/usr/bin/env python3
import argparse
from discord_qna_bot.oauth_server import start_server
from discord_qna_bot.config import settings

def main():
    parser = argparse.ArgumentParser(description="Run the Discord OAuth server")
    parser.add_argument("--host", default=None, help="Host to bind the server to (overrides config)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind the server to (overrides config)")
    
    args = parser.parse_args()
    
    # Use command line args if provided, otherwise use settings
    host = args.host or settings.host
    port = args.port or settings.port
    
    print(f"Starting Discord OAuth server on {host}:{port}")
    start_server(host=host, port=port)

if __name__ == "__main__":
    main()
