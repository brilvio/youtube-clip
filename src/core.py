from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

def parse_timestamp(value: str) -> int:
    """Convert MM:SS or HH:MM:SS into seconds."""
    value = value.strip()
    parts = value.split(":")
    if len(parts) not in (2, 3) or not all(part.isdigit() for part in parts):
        raise ValueError("Use o formato MM:SS ou HH:MM:SS (ex.: 1:00).")
    numbers = [int(part) for part in parts]
    if len(numbers) == 2:
        minutes, seconds = numbers
        if seconds >= 60:
            raise ValueError("Os segundos devem estar entre 00 e 59.")
        return minutes * 60 + seconds
    hours, minutes, seconds = numbers
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Minutos e segundos devem estar entre 00 e 59.")
    return hours * 3600 + minutes * 60 + seconds


def normalize_timestamp(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def validate_url(url: str) -> None:
    if not re.match(r"^https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/", url.strip()):
        raise ValueError("Informe uma URL válida do YouTube.")


@dataclass(frozen=True)
class ClipRequest:
    url: str
    start: int
    end: int
    output_dir: Path

    @classmethod
    def create(cls, url: str, start: str, end: str, output_dir: Path) -> "ClipRequest":
        validate_url(url)
        start_seconds = parse_timestamp(start)
        end_seconds = parse_timestamp(end)
        if end_seconds <= start_seconds:
            raise ValueError("O timestamp final deve ser maior que o inicial.")
        return cls(url.strip(), start_seconds, end_seconds, output_dir)


def extract_clip(request: ClipRequest, log: Callable[[str], None]) -> None:
    request.output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError("FFmpeg não está instalado. Instale-o antes de continuar.")
    section = f"*{normalize_timestamp(request.start)}-{normalize_timestamp(request.end)}"
    common = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--newline",
        "--no-playlist",
        "--download-sections",
        section,
        "--force-keyframes-at-cuts",
        "--ffmpeg-location",
        ffmpeg_path,
    ]
    jobs = [
        (
            "vídeo",
            common
            + [
                "--merge-output-format",
                "mp4",
                "-f",
                "bv*+ba/b",
                "-o",
                str(request.output_dir / "%(title).180B [trecho].%(ext)s"),
                request.url,
            ],
        ),
        (
            "áudio",
            common
            + [
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
                "-o",
                str(request.output_dir / "%(title).180B [áudio].%(ext)s"),
                request.url,
            ],
        ),
    ]
    for label, command in jobs:
        log(f"Preparando {label}...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if line:
                log(line)
        if process.wait() != 0:
            raise RuntimeError(f"Falha ao extrair {label}. Consulte o log acima.")
