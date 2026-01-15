#!/usr/bin/env python3
"""DropVox - macOS menu bar audio transcription."""

from dropvox.app import DropVoxApp


def main():
    """Run the DropVox menu bar application."""
    app = DropVoxApp()
    app.run()


if __name__ == "__main__":
    main()
