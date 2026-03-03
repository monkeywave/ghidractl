"""Allow running ghidractl as `python -m ghidractl`."""

from ghidractl.cli.app import app

if __name__ == "__main__":
    app()
