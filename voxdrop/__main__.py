#!/usr/bin/env python3
"""VoxDrop - macOS menu bar audio transcription."""

from voxdrop.app import VoxDropApp


def main():
    """Run the VoxDrop menu bar application."""
    app = VoxDropApp()
    app.run()


if __name__ == "__main__":
    main()
