"""Cross-platform helpers for title-derived output paths."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_WINDOWS_RESERVED = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE)
_DASHES = re.compile(r"-+")


def _utf16_units(value: str) -> int:
    return sum(2 if ord(char) > 0xFFFF else 1 for char in value)


def _truncate_utf16(value: str, max_units: int) -> str:
    used = 0
    result = []
    for char in value:
        units = 2 if ord(char) > 0xFFFF else 1
        if used + units > max_units:
            break
        result.append(char)
        used += units
    return "".join(result)


def safe_component(value: str, *, max_length: int = 120, fallback: str = "untitled") -> str:
    """Return a bounded Windows-safe path component (max_length UTF-16 code units)."""
    max_length = max(1, max_length)
    normalized = unicodedata.normalize("NFC", str(value))
    chars = []
    for char in normalized:
        category = unicodedata.category(char)
        chars.append(char if category[0] in {"L", "N", "M"} or char in " -_.()" else "-")
    value = _DASHES.sub("-", "".join(chars)).strip(" .-")
    if not value:
        value = _DASHES.sub("-", str(fallback)).strip(" .-") or "untitled"
    if _WINDOWS_RESERVED.match(value):
        value = f"_{value}"
    value = _truncate_utf16(value, max_length).rstrip(" .-")
    if not value:
        value = _truncate_utf16("untitled", max_length)
    if _WINDOWS_RESERVED.match(value):
        value = _truncate_utf16(f"_{value}", max_length)
    return value


def video_folder_name(title: str, video_id: str, *, max_length: int = 160) -> str:
    """Use the ID as a stable uniqueness suffix within a UTF-16-unit budget."""
    max_length = max(1, max_length)
    if max_length < 3:
        return safe_component(video_id, max_length=max_length, fallback="v")
    suffix = safe_component(video_id, max_length=min(32, max_length - 2), fallback="v")
    title_limit = max_length - _utf16_units(suffix) - 1
    clean_title = safe_component(title, max_length=title_limit)
    return f"{clean_title}-{suffix}"


def report_path(folder: str | Path) -> Path:
    """Return the folder-matching Markdown report path."""
    directory = Path(folder)
    suffix = ".md"
    return directory / f"{safe_component(directory.name, max_length=180 - _utf16_units(suffix))}{suffix}"


def project_path(path: str | Path) -> Path:
    """Resolve relative project paths from the repository, not the caller's cwd."""
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
