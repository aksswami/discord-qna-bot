#!/usr/bin/env python3
import argparse
from discord_qna_bot.oauth_server import start_server

def main():
    parser = argparse.ArgumentParser(description="Run the Discord OAuth server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    
    args = parser.parse_args()
    
    print(f"Starting Discord OAuth server on {args.host}:{args.port}")
    start_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
