"""Provider-neutral intake for raster concept exploration, never for masters."""
from pathlib import Path

from contracts import digest, require

MAX_BYTES = 20 * 1024 * 1024


def record(path: Path, provider: str, observation: str, rights: str) -> dict[str, str]:
    require(path.is_file() and not path.is_symlink(), "Provide a regular local raster file")
    require(all(value.strip() for value in (provider, observation, rights)),
            "Record provider, observation and usage rights")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, "Raster reference exceeds 20 MiB")
    raster_format(data)
    return {"kind": "generated-image",
            "source": f"{provider} / {path.name} / SHA-256 {digest(data)}",
            "observation": observation, "rights": rights}


def raster_format(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return "jpg"
    raise ValueError("Expected PNG or JPEG raster reference")
