from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.config import SAMPLE_IMAGES_DIR

_SAMPLE_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+\.(?:jpe?g|png|webp|gif)$", re.IGNORECASE)
_EXT_MEDIA = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def list_sample_images() -> list[dict[str, str]]:
    if not SAMPLE_IMAGES_DIR.is_dir():
        return []
    names: list[str] = []
    for pattern in ("*.jpeg", "*.jpg", "*.JPEG", "*.JPG"):
        names.extend(p.name for p in SAMPLE_IMAGES_DIR.glob(pattern))
    out: list[dict[str, str]] = []
    for name in sorted(set(names), key=lambda n: (len(n), n)):
        stem = Path(name).stem
        out.append(
            {
                "name": name,
                "label": stem,
                "url": f"/api/samples/{name}",
            }
        )
    return out


def resolve_sample_path(filename: str) -> Path:
    if not _SAMPLE_NAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid sample filename")
    base = SAMPLE_IMAGES_DIR.resolve()
    path = (SAMPLE_IMAGES_DIR / filename).resolve()
    if base not in path.parents and path != base:
        raise HTTPException(status_code=400, detail="Invalid sample path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sample not found")
    return path


def sample_file_response(path: Path) -> FileResponse:
    media = _EXT_MEDIA.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media, filename=path.name)
