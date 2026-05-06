"""
Tests for transcription service.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from app.services.transcription import (
    chunk_transcript,
    get_file_type,
    extract_audio_from_video,
    split_audio_file,
    transcribe_audio,
    transcribe_media_file,
)


class TestGetFileType:
    def test_audio_files(self):
        assert get_file_type("test.mp3") == "audio"
        assert get_file_type("test.wav") == "audio"
        assert get_file_type("test.m4a") == "audio"

    def test_video_files(self):
        assert get_file_type("test.mp4") == "video"
        # .webm is in both SUPPORTED_AUDIO_EXTENSIONS and SUPPORTED_VIDEO_EXTENSIONS
        # The implementation checks audio first, so .webm is classified as audio
        assert get_file_type("test.webm") == "audio"
        assert get_file_type("test.mov") == "video"

    def test_unsupported_extension(self):
        with pytest.raises(ValueError):
            get_file_type("test.txt")


class TestChunkTranscript:
    def test_chunks_transcript(self, sample_transcript):
        chunks = chunk_transcript(sample_transcript, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source_type"] == "media"
            assert "start_time" in chunk["metadata"]
            assert "end_time" in chunk["metadata"]

    def test_empty_transcript(self):
        chunks = chunk_transcript({"segments": [], "full_text": ""})
        assert chunks == []

    def test_preserves_timestamps(self, sample_transcript):
        chunks = chunk_transcript(sample_transcript, chunk_size=1000, chunk_overlap=0)
        assert chunks[0]["metadata"]["start_time"] == 0.0
        assert chunks[-1]["metadata"]["end_time"] > 0


class TestExtractAudioFromVideo:
    def test_extracts_audio_using_ffmpeg(self):
        with patch("app.services.transcription.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            result = extract_audio_from_video("/tmp/video.mp4", "/tmp/output.mp3")

            assert result == "/tmp/output.mp3"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ffmpeg" in args
            assert "-vn" in args  # No video flag

    def test_raises_on_ffmpeg_failure(self):
        with patch("app.services.transcription.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")

            with pytest.raises(RuntimeError, match="ffmpeg failed"):
                extract_audio_from_video("/tmp/video.mp4")

    def test_uses_temp_file_when_no_output_path(self):
        with patch("app.services.transcription.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            with patch("tempfile.mktemp") as mock_temp:
                mock_temp.return_value = "/tmp/temp_audio.mp3"

                result = extract_audio_from_video("/tmp/video.mp4")

                assert result == "/tmp/temp_audio.mp3"


class TestSplitAudioFile:
    def test_returns_single_file_if_under_size_limit(self):
        with patch("os.path.getsize") as mock_size:
            mock_size.return_value = 10 * 1024 * 1024  # 10 MB

            result = split_audio_file("/tmp/audio.mp3", max_size_mb=25)

            assert result == ["/tmp/audio.mp3"]

    def test_splits_large_files(self):
        with patch("os.path.getsize") as mock_size:
            mock_size.return_value = 50 * 1024 * 1024  # 50 MB

            with patch("app.services.transcription.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="300.0",  # 5 minutes duration
                    stderr="",
                )

                result = split_audio_file("/tmp/audio.mp3", max_size_mb=25)

                # Should split into at least 2 chunks
                assert len(result) >= 2
                mock_run.assert_called()


class TestTranscribeAudio:
    @pytest.mark.asyncio
    async def test_transcribes_with_whisper_api(self):
        mock_response = MagicMock()
        mock_response.segments = [
            MagicMock(start=0.0, end=5.0, text="Hello world"),
        ]
        mock_response.text = "Hello world"
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.transcription.AsyncOpenAI", return_value=mock_client):
            with patch("os.path.getsize") as mock_size:
                mock_size.return_value = 5 * 1024 * 1024  # 5 MB

                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(b"fake audio data")
                    temp_path = f.name

                try:
                    result = await transcribe_audio(temp_path)

                    assert "segments" in result
                    assert "full_text" in result
                    assert len(result["segments"]) == 1
                    assert result["segments"][0]["text"] == "Hello world"
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)


class TestTranscribeMediaFile:
    @pytest.mark.asyncio
    async def test_transcribes_audio_file_directly(self):
        mock_response = MagicMock()
        mock_response.segments = [
            MagicMock(start=0.0, end=5.0, text="Hello"),
        ]
        mock_response.text = "Hello"
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.transcription.AsyncOpenAI", return_value=mock_client):
            with patch("os.path.getsize") as mock_size:
                mock_size.return_value = 5 * 1024 * 1024

                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(b"fake audio data")
                    temp_path = f.name

                try:
                    result = await transcribe_media_file(temp_path)

                    assert "segments" in result
                    assert result["full_text"] == "Hello"
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_extracts_and_transcribes_video(self):
        mock_response = MagicMock()
        mock_response.segments = [
            MagicMock(start=0.0, end=5.0, text="Video content"),
        ]
        mock_response.text = "Video content"
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.transcription.AsyncOpenAI", return_value=mock_client):
            with patch(
                "app.services.transcription.extract_audio_from_video"
            ) as mock_extract:
                with tempfile.NamedTemporaryFile(
                    suffix=".mp3", delete=False
                ) as audio_f:
                    audio_f.write(b"extracted audio")
                    audio_path = audio_f.name

                mock_extract.return_value = audio_path

                with patch("os.path.getsize") as mock_size:
                    mock_size.return_value = 5 * 1024 * 1024

                    with tempfile.NamedTemporaryFile(
                        suffix=".mp4", delete=False
                    ) as video_f:
                        video_f.write(b"video data")
                        video_path = video_f.name

                    try:
                        result = await transcribe_media_file(video_path)

                        assert "segments" in result
                        mock_extract.assert_called_once_with(video_path)
                    finally:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
                        if os.path.exists(audio_path):
                            os.unlink(audio_path)
