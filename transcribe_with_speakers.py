#!/usr/bin/env python3
"""Local speaker-aware transcription pipeline.

This script keeps recordings local. It downloads open model weights when needed,
but it does not upload the recording to a paid API or external transcription
service.
"""

from __future__ import annotations

import argparse
import gc
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from utils.formatting import (
    TranscriptSegment,
    clean_text,
    write_readable_transcript,
    write_segments_json,
    write_speaker_mapping_template,
    write_srt,
)


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".wav", ".mp3", ".m4a"}
SUPPORTED_MODELS = ("small", "medium", "large-v3")
CUDA_ONLY_COMPUTE_TYPES = {"float16", "int8_float16"}


class PipelineError(Exception):
    """A beginner-friendly error that can be printed directly."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a local video or audio file into a timestamped transcript "
            "with anonymous speaker labels."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help=(
            "Path to one input recording, or a folder containing recordings to "
            "process in batch."
        ),
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Folder where transcript output files will be saved.",
    )
    parser.add_argument(
        "--model",
        choices=SUPPORTED_MODELS,
        default="large-v3",
        help="Whisper model size. Default: large-v3.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language code such as en or zh. If empty, language is detected.",
    )
    parser.add_argument(
        "--min_speakers",
        type=positive_int,
        default=None,
        help="Optional minimum number of speakers.",
    )
    parser.add_argument(
        "--max_speakers",
        type=positive_int,
        default=None,
        help="Optional maximum number of speakers.",
    )
    parser.add_argument(
        "--compute_type",
        default=None,
        help=(
            "Optional compute type, such as float16, int8, or float32. "
            "If empty, float16 is used with CUDA and int8 is used on CPU."
        ),
    )
    parser.add_argument(
        "--hf_token",
        default=None,
        help="Optional Hugging Face token. If empty, HF_TOKEN is read from the environment.",
    )

    args = parser.parse_args()
    if (
        args.min_speakers is not None
        and args.max_speakers is not None
        and args.min_speakers > args.max_speakers
    ):
        raise PipelineError(
            "Invalid speaker range.\n\n"
            "What to do next: make sure --min_speakers is less than or equal to "
            "--max_speakers. For example: --min_speakers 2 --max_speakers 4"
        )
    return args


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a whole number") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return parsed


def resolve_input_files(input_arg: str) -> tuple[list[Path], bool]:
    input_path = Path(input_arg).expanduser()
    if not input_path.exists():
        raise PipelineError(
            "Input file not found.\n\n"
            f"The file does not exist: {input_path}\n\n"
            "What to do next: check the path after --input. You can pass one file, "
            "such as data/meeting.mp4, or a folder, such as data."
        )

    if input_path.is_dir():
        input_files = sorted(
            (
                child
                for child in input_path.iterdir()
                if child.is_file() and is_supported_media_file(child)
            ),
            key=lambda path: path.name.lower(),
        )
        if not input_files:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise PipelineError(
                "No supported recordings found.\n\n"
                f"The folder does not contain supported recording files: {input_path}\n"
                f"This tool supports: {supported}\n\n"
                "What to do next: put recordings such as meeting.mp4, meeting.wav, "
                "or interview.m4a directly inside the folder, then run again."
            )
        return input_files, True

    if not input_path.is_file():
        raise PipelineError(
            "Input path is not a file or folder.\n\n"
            f"The path points to something unsupported: {input_path}\n\n"
            "What to do next: pass the path to one recording file, such as "
            "data/meeting.mp4, or a folder, such as data."
        )

    if not is_supported_media_file(input_path):
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise PipelineError(
            "Unsupported file format.\n\n"
            f"This tool supports: {supported}\n"
            f"Your file extension was: {input_path.suffix or '(no extension)'}\n\n"
            "What to do next: convert the recording to one of the supported formats, "
            "or choose a supported input file."
        )

    return [input_path], False


def is_supported_media_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def batch_output_folder_name(input_path: Path) -> str:
    return input_path.name.replace(".", "_")


def validate_batch_output_folder_names(input_files: list[Path]) -> None:
    seen: dict[str, Path] = {}
    for input_file in input_files:
        folder_name = batch_output_folder_name(input_file)
        if folder_name in seen:
            raise PipelineError(
                "Batch output folder name conflict.\n\n"
                "Two input files would use the same output folder name after replacing "
                "dots with underscores:\n\n"
                f"  {seen[folder_name]}\n"
                f"  {input_file}\n\n"
                f"Both would write to a folder named: {folder_name}\n\n"
                "What to do next: rename one of the input files, then run again."
            )
        seen[folder_name] = input_file


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise PipelineError(
            "ffmpeg not found.\n\n"
            "This tool needs ffmpeg to read audio and video files.\n\n"
            "What to do next: install ffmpeg, then run this command to check it:\n"
            "  ffmpeg -version\n\n"
            "On macOS with Homebrew, use:\n"
            "  brew install ffmpeg\n\n"
            "On Ubuntu, use:\n"
            "  sudo apt update\n"
            "  sudo apt install ffmpeg\n\n"
            "On Windows, install ffmpeg and make sure it is available in PowerShell."
        )


def prepare_output_dir(output_arg: str | Path) -> Path:
    output_dir = Path(output_arg).expanduser()
    if output_dir.exists() and not output_dir.is_dir():
        raise PipelineError(
            "Invalid output folder.\n\n"
            f"This path already exists but it is not a folder: {output_dir}\n\n"
            "What to do next: choose a different --output_dir, or remove/rename the "
            "file that is using this path."
        )

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PipelineError(
            "Invalid output folder.\n\n"
            f"The folder could not be created: {output_dir}\n\n"
            "What to do next: choose a folder where you have permission to write, "
            "such as outputs/meeting."
        ) from exc

    return output_dir


def load_dotenv_if_present() -> None:
    """Load HF_TOKEN from a local .env file if the shell environment is empty."""
    if os.environ.get("HF_TOKEN"):
        return

    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "HF_TOKEN":
            continue
        token = value.strip().strip('"').strip("'")
        if token:
            os.environ["HF_TOKEN"] = token
        return


def get_hf_token(cli_token: str | None) -> str:
    token = cli_token or os.environ.get("HF_TOKEN")
    if not token:
        raise PipelineError(
            "Hugging Face token missing.\n\n"
            "Speaker diarization needs a free Hugging Face Read token so it can "
            "download the pyannote speaker model to your computer.\n\n"
            "What to do next: follow Section 7 in README.md, then run the command "
            "again. You can set the token with:\n\n"
            'macOS / Linux:\n  export HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"\n\n'
            'Windows PowerShell:\n  $env:HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"'
        )
    return token


def import_runtime_dependencies() -> tuple[Any, Any, Any]:
    # Disable optional pyannote telemetry for a privacy-first local workflow.
    os.environ["PYANNOTE_METRICS_ENABLED"] = "0"

    try:
        import torch
    except ModuleNotFoundError as exc:
        raise PipelineError(
            "A required Python package is missing: torch.\n\n"
            "What to do next: activate your virtual environment and run:\n"
            "  pip install -r requirements.txt"
        ) from exc

    try:
        import whisperx
    except ModuleNotFoundError as exc:
        raise PipelineError(
            "A required Python package is missing: whisperx.\n\n"
            "What to do next: activate your virtual environment and run:\n"
            "  pip install -r requirements.txt"
        ) from exc

    try:
        from whisperx.diarize import DiarizationPipeline
    except ModuleNotFoundError as exc:
        raise PipelineError(
            "A required Python package for speaker diarization is missing.\n\n"
            "What to do next: activate your virtual environment and run:\n"
            "  pip install -r requirements.txt"
        ) from exc

    return torch, whisperx, DiarizationPipeline


def choose_device_and_compute_type(torch: Any, requested_compute_type: str | None) -> tuple[str, str]:
    cuda_available = bool(torch.cuda.is_available())
    device = "cuda" if cuda_available else "cpu"
    compute_type = requested_compute_type or ("float16" if cuda_available else "int8")

    if not cuda_available and compute_type.lower() in CUDA_ONLY_COMPUTE_TYPES:
        raise PipelineError(
            "CUDA unavailable.\n\n"
            f"You asked for --compute_type {compute_type}, but this computer does not "
            "currently have an available CUDA NVIDIA GPU.\n\n"
            "What to do next: run the command without --compute_type so the script "
            "can use int8 on CPU, or use:\n"
            "  --compute_type int8\n\n"
            "CPU mode works, but it is usually much slower than GPU mode."
        )

    return device, compute_type


def transcribe_audio(
    torch: Any,
    whisperx: Any,
    audio: Any,
    model_name: str,
    language: str | None,
    device: str,
    compute_type: str,
) -> dict[str, Any]:
    print("Running transcription...")
    batch_size = 16 if device == "cuda" else 4
    model = None

    try:
        model = whisperx.load_model(
            model_name,
            device,
            compute_type=compute_type,
            language=language,
        )
        result = model.transcribe(audio, batch_size=batch_size, language=language)
    except Exception as exc:
        raise PipelineError(
            "Transcription failure.\n\n"
            "The recording could not be converted to text.\n\n"
            "What to do next: check that the file plays correctly, try a smaller "
            "model such as --model medium, or use --compute_type int8.\n\n"
            f"Technical detail: {exc}"
        ) from exc
    finally:
        del model
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

    if not has_text_segments(result):
        raise PipelineError(
            "Empty transcript.\n\n"
            "The transcription step finished, but it did not find any spoken text.\n\n"
            "What to do next: check that the recording has audible speech, that the "
            "audio is not muted, and that the input file is the correct recording."
        )

    return result


def align_transcript(
    torch: Any,
    whisperx: Any,
    transcription_result: dict[str, Any],
    audio: Any,
    language: str | None,
    device: str,
) -> dict[str, Any]:
    print("Running alignment...")
    language_code = language or transcription_result.get("language")
    if not language_code:
        raise PipelineError(
            "Alignment failure.\n\n"
            "The language could not be detected, so the timestamp alignment model "
            "could not be selected.\n\n"
            "What to do next: run the command again with --language, for example "
            "--language en or --language zh."
        )

    try:
        model_a = None
        model_a, metadata = whisperx.load_align_model(
            language_code=language_code,
            device=device,
        )
        aligned_result = whisperx.align(
            transcription_result["segments"],
            model_a,
            metadata,
            audio,
            device,
            return_char_alignments=False,
        )
        return aligned_result
    except Exception as exc:
        raise PipelineError(
            "Alignment failure.\n\n"
            "The text was transcribed, but the script could not align the words to "
            "precise timestamps.\n\n"
            "What to do next: try setting --language explicitly. If the recording is "
            "in a less common language, WhisperX may not have a built-in alignment "
            "model for that language.\n\n"
            f"Technical detail: {exc}"
        ) from exc
    finally:
        del model_a
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()


def create_diarization_pipeline(
    DiarizationPipeline: Any,
    hf_token: str,
    device: str,
) -> Any:
    try:
        return DiarizationPipeline(token=hf_token, device=device)
    except TypeError:
        return DiarizationPipeline(use_auth_token=hf_token, device=device)


def diarize_and_assign_speakers(
    whisperx: Any,
    DiarizationPipeline: Any,
    aligned_result: dict[str, Any],
    audio: Any,
    hf_token: str,
    device: str,
    min_speakers: int | None,
    max_speakers: int | None,
) -> dict[str, Any]:
    print("Running speaker diarization...")
    speaker_kwargs: dict[str, int] = {}
    if min_speakers is not None:
        speaker_kwargs["min_speakers"] = min_speakers
    if max_speakers is not None:
        speaker_kwargs["max_speakers"] = max_speakers

    try:
        diarize_model = create_diarization_pipeline(DiarizationPipeline, hf_token, device)
        diarize_segments = diarize_model(audio, **speaker_kwargs)
        print("Assigning speaker labels...")
        return whisperx.assign_word_speakers(diarize_segments, aligned_result)
    except Exception as exc:
        if looks_like_access_denied(exc):
            raise PipelineError(
                "pyannote model access denied.\n\n"
                "The Hugging Face token was found, but it could not download the "
                "pyannote speaker diarization model.\n\n"
                "What to do next:\n"
                "1. Log in to Hugging Face using the same account that created the token.\n"
                "2. Open https://huggingface.co/pyannote/speaker-diarization-community-1\n"
                "3. Click Access repository or Agree and access repository.\n"
                "4. If Hugging Face asks you to accept another related pyannote model, "
                "such as pyannote/speaker-diarization-3.1, accept that model too.\n"
                "5. Make sure your token has Read permission, then run the command again.\n\n"
                f"Technical detail: {exc}"
            ) from exc

        raise PipelineError(
            "Diarization failure.\n\n"
            "The text was transcribed, but the script could not separate the speakers.\n\n"
            "What to do next: check your Hugging Face token, accept the pyannote model "
            "terms, and try setting --min_speakers and --max_speakers if you know how "
            "many people are in the recording.\n\n"
            f"Technical detail: {exc}"
        ) from exc


def looks_like_access_denied(exc: Exception) -> bool:
    text = str(exc).lower()
    access_markers = (
        "401",
        "403",
        "access",
        "authorization",
        "authorized",
        "forbidden",
        "gated",
        "private",
        "repository not found",
        "token",
        "unauthorized",
    )
    return any(marker in text for marker in access_markers)


def has_text_segments(result: dict[str, Any]) -> bool:
    return any(clean_text(str(segment.get("text", ""))) for segment in result.get("segments", []))


def speaker_from_words(words: Any) -> str | None:
    if not isinstance(words, list):
        return None

    speakers = [
        str(word["speaker"])
        for word in words
        if isinstance(word, dict) and word.get("speaker")
    ]
    if not speakers:
        return None
    return Counter(speakers).most_common(1)[0][0]


def normalize_speaker_segments(raw_segments: list[dict[str, Any]]) -> list[TranscriptSegment]:
    speaker_map: dict[str, str] = {}
    normalized: list[TranscriptSegment] = []
    saw_diarized_speaker = False

    for raw_segment in raw_segments:
        text = clean_text(str(raw_segment.get("text", "")))
        if not text:
            continue

        raw_speaker = raw_segment.get("speaker") or speaker_from_words(
            raw_segment.get("words", [])
        )
        if raw_speaker:
            saw_diarized_speaker = True
            raw_speaker_key = str(raw_speaker)
        else:
            raw_speaker_key = "UNASSIGNED"

        if raw_speaker_key not in speaker_map:
            speaker_map[raw_speaker_key] = f"SPEAKER_{len(speaker_map):02d}"

        start = safe_float(raw_segment.get("start"), default=0.0)
        end = safe_float(raw_segment.get("end"), default=start)
        if end < start:
            end = start

        normalized.append(
            {
                "speaker": speaker_map[raw_speaker_key],
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
            }
        )

    if not normalized:
        raise PipelineError(
            "Empty transcript.\n\n"
            "The pipeline finished, but there were no transcript segments to save.\n\n"
            "What to do next: check that the recording has audible speech and try again."
        )

    if not saw_diarized_speaker:
        raise PipelineError(
            "Diarization failure.\n\n"
            "The speaker diarization step finished, but no speaker labels were assigned "
            "to the transcript.\n\n"
            "What to do next: check that the recording has clear speech, try setting "
            "--min_speakers and --max_speakers, or try a cleaner audio file."
        )

    return normalized


def safe_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def save_outputs(
    segments: list[TranscriptSegment],
    output_dir: Path,
    recording_id: str,
) -> None:
    print("Saving output files...")
    speakers = [str(segment["speaker"]) for segment in segments]

    try:
        write_segments_json(segments, output_dir / "transcript_segments.json")
        write_readable_transcript(segments, output_dir / "transcript_readable.txt")
        write_srt(segments, output_dir / "transcript.srt")
        write_speaker_mapping_template(
            recording_id,
            speakers,
            output_dir / "speaker_role_mapping_template.json",
        )
    except OSError as exc:
        raise PipelineError(
            "Invalid output folder.\n\n"
            "The transcript was created, but the output files could not be written.\n\n"
            f"Folder: {output_dir}\n\n"
            "What to do next: choose a folder where you have permission to write, "
            "such as outputs/meeting.\n\n"
            f"Technical detail: {exc}"
        ) from exc


def process_recording(
    input_path: Path,
    output_dir: Path,
    torch: Any,
    whisperx: Any,
    DiarizationPipeline: Any,
    hf_token: str,
    device: str,
    compute_type: str,
    model_name: str,
    language: str | None,
    min_speakers: int | None,
    max_speakers: int | None,
) -> None:
    output_dir = prepare_output_dir(output_dir)
    print(f"Input file: {input_path}")
    print(f"Output folder: {output_dir}")
    print("Loading audio...")
    try:
        audio = whisperx.load_audio(str(input_path))
    except Exception as exc:
        raise PipelineError(
            "Transcription failure.\n\n"
            "The recording could not be loaded.\n\n"
            "What to do next: make sure the file is not corrupted and that ffmpeg "
            "can open it. You can test ffmpeg with:\n"
            f"  ffmpeg -i \"{input_path}\"\n\n"
            f"Technical detail: {exc}"
        ) from exc

    transcription_result = transcribe_audio(
        torch,
        whisperx,
        audio,
        model_name=model_name,
        language=language,
        device=device,
        compute_type=compute_type,
    )
    aligned_result = align_transcript(
        torch,
        whisperx,
        transcription_result,
        audio,
        language=language,
        device=device,
    )
    speaker_result = diarize_and_assign_speakers(
        whisperx,
        DiarizationPipeline,
        aligned_result,
        audio,
        hf_token,
        device,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

    segments = normalize_speaker_segments(speaker_result.get("segments", []))
    save_outputs(segments, output_dir, recording_id=input_path.stem)


def run() -> None:
    args = parse_args()
    input_files, is_batch = resolve_input_files(args.input)
    if is_batch:
        validate_batch_output_folder_names(input_files)

    check_ffmpeg()
    base_output_dir = prepare_output_dir(args.output_dir)
    load_dotenv_if_present()
    hf_token = get_hf_token(args.hf_token)

    torch, whisperx, DiarizationPipeline = import_runtime_dependencies()
    device, compute_type = choose_device_and_compute_type(torch, args.compute_type)

    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        print(f"CUDA GPU detected: {gpu_name}")
    else:
        print("CUDA GPU not detected. Using CPU mode. This may be slow.")
    print(f"Using compute type: {compute_type}")

    if is_batch:
        print(f"Batch mode detected. Found {len(input_files)} supported recording(s).")

    for index, input_path in enumerate(input_files, start=1):
        if is_batch:
            print("")
            print(f"Processing recording {index} of {len(input_files)}: {input_path.name}")
            output_dir = base_output_dir / batch_output_folder_name(input_path)
        else:
            output_dir = base_output_dir

        process_recording(
            input_path,
            output_dir,
            torch,
            whisperx,
            DiarizationPipeline,
            hf_token,
            device,
            compute_type,
            model_name=args.model,
            language=args.language,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
        )

    print("Done.")
    print(f"Output files saved to: {base_output_dir}")


def main() -> int:
    try:
        run()
    except PipelineError as exc:
        print(f"\nERROR: {exc}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped by user.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
