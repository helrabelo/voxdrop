"""Tests for the transcriber module."""

from pathlib import Path

import pytest

from voxdrop.transcriber import SUPPORTED_FORMATS, is_supported_format


class TestSupportedFormats:
    """Test format validation."""

    def test_opus_supported(self):
        """WhatsApp default format should be supported."""
        assert is_supported_format(Path("audio.opus"))

    def test_mp3_supported(self):
        """MP3 format should be supported."""
        assert is_supported_format(Path("audio.mp3"))

    def test_m4a_supported(self):
        """M4A format should be supported."""
        assert is_supported_format(Path("audio.m4a"))

    def test_wav_supported(self):
        """WAV format should be supported."""
        assert is_supported_format(Path("audio.wav"))

    def test_uppercase_extension(self):
        """Uppercase extensions should be supported."""
        assert is_supported_format(Path("audio.OPUS"))
        assert is_supported_format(Path("audio.MP3"))

    def test_unsupported_format(self):
        """Unsupported formats should be rejected."""
        assert not is_supported_format(Path("audio.txt"))
        assert not is_supported_format(Path("audio.pdf"))
        assert not is_supported_format(Path("audio.aac"))

    def test_all_formats_in_constant(self):
        """All formats in SUPPORTED_FORMATS should work."""
        for fmt in SUPPORTED_FORMATS:
            assert is_supported_format(Path(f"test{fmt}"))


# Note: Integration tests with actual Whisper transcription
# require audio fixtures and are run manually
