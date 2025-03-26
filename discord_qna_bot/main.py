# -*- coding: utf-8 -*-
"""Main entry point for the discord-qna-bot CLI."""

import sys


def main(args=None):
    """
    Main function for the CLI.

    Args:
        args (list, optional): Command line arguments. Defaults to None.
    """
    if args is None:
        args = sys.argv[1:]

    print("Hello from discord-qna-bot!")
    print(f"Arguments received: {args}")
    # TODO: Add actual CLI logic here using argparse or a library like Typer/Click


if __name__ == "__main__":
    main()
