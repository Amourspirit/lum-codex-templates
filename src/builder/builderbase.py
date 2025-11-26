from pathlib import Path
import hashlib
from ..config.pkg_config import PkgConfig


class BuilderBase:
    def __init__(self):
        self.config = PkgConfig()

    def compute_sha256(self, file_path: Path | str) -> str:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
