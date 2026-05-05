"""
Audio/Video transcription service using OpenAI Whisper API.
"""

import os
import math
import tempfile
import subprocess
from pathlib import Path

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()

# Whisper API max file size is 25MB
MAX_CHUNK_SIZE_MB = 24

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


def get_file_type(file_path: str) -> str:
    """Determine if a file is audio or video based on extension."""
    ext = Path(file_path).suffix.lower()
    if ext in SUPPORTED_AUDIO_EXTENSIONS:
        return "audio"
    elif ext in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    raise ValueError(f"Unsupported media file extension: {ext}")


def extract_audio_from_video(video_path: str, output_path: str | None = None) -> str:
    """Extract audio track from a video file using ffmpeg.

    Args:
        video_path: Path to the video file.
        output_path: Optional output path. Defaults to temp file.

    Returns:
        Path to the extracted audio file.
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",  # No video
        "-acodec", "libmp3lame",
        "-ar", "16000",  # 16kHz sample rate for Whisper
        "-ac", "1",  # Mono
        "-y",  # Overwrite
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    return output_path


def split_audio_file(audio_path: str, max_size_mb: int = MAX_CHUNK_SIZE_MB) -> list[str]:
    """Split large audio file into smaller chunks for Whisper API.

    Args:
        audio_path: Path to the audio file.
        max_size_mb: Maximum chunk size in MB.

    Returns:
        List of paths to audio chunks.
    """
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    if file_size_mb <= max_size_mb:
        return [audio_path]

    # Get audio duration
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())

    # Calculate number of chunks
    num_chunks = math.ceil(file_size_mb / max_size_mb)
    chunk_duration = duration / num_chunks

    chunks = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_path = tempfile.mktemp(suffix=f"_chunk_{i}.mp3")

        cmd = [
            "ffmpeg", "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            "-acodec", "libmp3lame",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            chunk_path,
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        chunks.append(chunk_path)

    return chunks


async def transcribe_audio(audio_path: str) -> dict:
    """Transcribe audio file using OpenAI Whisper API with timestamps.

    Args:
        audio_path: Path to the audio file.

    Returns:
        Dict with 'segments' and 'full_text' keys.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Split if file is too large
    chunks = split_audio_file(audio_path)

    all_segments = []
    full_text_parts = []
    time_offset = 0.0

    for chunk_path in chunks:
        with open(chunk_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"],
            )

        # Process segments with time offset
        for segment in response.segments:
            adjusted_segment = {
                "id": len(all_segments),
                "start": segment.start + time_offset,
                "end": segment.end + time_offset,
                "text": segment.text.strip(),
            }

            # Add word-level timestamps if available
            if hasattr(response, "words") and response.words:
                adjusted_segment["words"] = [
                    {
                        "word": w.word,
                        "start": w.start + time_offset,
                        "end": w.end + time_offset,
                    }
                    for w in response.words
                    if segment.start <= w.start <= segment.end
                ]

            all_segments.append(adjusted_segment)

        full_text_parts.append(response.text)

        # Update time offset for next chunk
        if all_segments:
            time_offset = all_segments[-1]["end"]

        # Clean up temp chunk files
        if chunk_path != audio_path:
            os.unlink(chunk_path)

    return {
        "segments": all_segments,
        "full_text": " ".join(full_text_parts),
    }


async def transcribe_media_file(file_path: str) -> dict:
    """Transcribe any audio or video file.

    For video files, extracts audio first, then transcribes.

    Args:
        file_path: Path to the media file.

    Returns:
        Transcription dict with segments and full text.
    """
    file_type = get_file_type(file_path)

    if file_type == "video":
        # Extract audio from video
        audio_path = extract_audio_from_video(file_path)
        try:
            result = await transcribe_audio(audio_path)
        finally:
            # Clean up extracted audio
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    else:
        result = await transcribe_audio(file_path)

    return result


def chunk_transcript(
    transcript: dict,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """Split transcript into chunks with timestamp metadata.

    Each chunk carries the start/end timestamps of its constituent segments.

    Args:
        transcript: Transcription result dict.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        List of chunk dicts with text and timestamp metadata.
    """
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    segments = transcript.get("segments", [])
    if not segments:
        return []

    # Build text with segment markers
    chunks = []
    current_text = ""
    current_segments = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    # Group segments into chunks
    for segment in segments:
        candidate = current_text + " " + segment["text"] if current_text else segment["text"]

        if len(candidate) > chunk_size and current_text:
            # Save current chunk
            chunks.append({
                "text": current_text.strip(),
                "metadata": {
                    "source_type": "media",
                    "start_time": current_segments[0]["start"],
                    "end_time": current_segments[-1]["end"],
                    "segment_ids": [s["id"] for s in current_segments],
                    "chunk_index": len(chunks),
                },
            })
            # Start new chunk with overlap
            overlap_segments = current_segments[-2:] if len(current_segments) > 2 else current_segments[-1:]
            current_text = " ".join(s["text"] for s in overlap_segments) + " " + segment["text"]
            current_segments = overlap_segments + [segment]
        else:
            current_text = candidate
            current_segments.append(segment)

    # Don't forget the last chunk
    if current_text.strip():
        chunks.append({
            "text": current_text.strip(),
            "metadata": {
                "source_type": "media",
                "start_time": current_segments[0]["start"],
                "end_time": current_segments[-1]["end"],
                "segment_ids": [s["id"] for s in current_segments],
                "chunk_index": len(chunks),
            },
        })

    return chunks
