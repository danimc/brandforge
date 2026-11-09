"""Local raster adapter. Only pass SVG composed from validated masters."""
from dataclasses import dataclass
import re
import shutil
import subprocess

from contracts import require


@dataclass(frozen=True)
class Rsvg:
    executable: str
    version: str

    @classmethod
    def discover(cls) -> "Rsvg":
        executable = shutil.which("rsvg-convert")
        require(executable, "Raster evidence requires librsvg (rsvg-convert on PATH)")
        version = cls.run([executable, "--version"]).decode("utf-8").strip()
        require(re.match(r"rsvg-convert version \d+\.\d+", version) is not None,
                "Unexpected rsvg-convert version output")
        return cls(executable, version)

    @staticmethod
    def run(args: list[str], data: bytes = b"") -> bytes:
        try:
            result = subprocess.run(args, input=data, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            raise ValueError("librsvg timed out") from error
        require(result.returncode == 0,
                f"librsvg failed: {result.stderr.decode('utf-8', errors='replace').strip()}")
        return result.stdout

    def png(self, sheet: bytes) -> bytes:
        data = self.run([self.executable, "--format=png"], sheet)
        require(data.startswith(b"\x89PNG\r\n\x1a\n"), "Renderer did not return PNG")
        return data
