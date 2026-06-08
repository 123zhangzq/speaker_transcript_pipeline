"""Output formatting helpers for transcript files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Sequence


TranscriptSegment = dict[str, Any]


def clean_text(text: str) -> str:
    """Normalize transcript text without changing the words."""
    return " ".join(text.strip().split())


def format_timestamp(seconds: float, *, decimal_separator: str = ".") -> str:
    """Format seconds as HH:MM:SS.mmm or HH:MM:SS,mmm."""
    milliseconds = int(round(max(seconds, 0.0) * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return (
        f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}"
        f"{decimal_separator}{millis:03d}"
    )


def write_segments_json(segments: Sequence[TranscriptSegment], output_path: Path) -> None:
    output_path.write_text(
        json.dumps(list(segments), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_readable_transcript(
    segments: Sequence[TranscriptSegment],
    output_path: Path,
) -> None:
    blocks: list[str] = []
    for segment in segments:
        start = format_timestamp(float(segment["start"]), decimal_separator=".")
        end = format_timestamp(float(segment["end"]), decimal_separator=".")
        blocks.append(f"[{start} - {end}] {segment['speaker']}:\n{segment['text']}")

    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_srt(segments: Sequence[TranscriptSegment], output_path: Path) -> None:
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        start = format_timestamp(float(segment["start"]), decimal_separator=",")
        end = format_timestamp(float(segment["end"]), decimal_separator=",")
        text = f"{segment['speaker']}: {segment['text']}"
        blocks.append(f"{index}\n{start} --> {end}\n{text}")

    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_speaker_mapping_template(
    recording_id: str,
    speakers: Iterable[str],
    output_path: Path,
) -> None:
    template = {
        "recording_id": recording_id,
        "speaker_role_mapping": {speaker: "" for speaker in sorted(set(speakers))},
    }
    output_path.write_text(
        json.dumps(template, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

