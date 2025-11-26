from pathlib import Path
import hashlib
import datetime
from ..config.pkg_config import PkgConfig


class BuilderBase:
    def __init__(self):
        self.config = PkgConfig()

    def compute_sha256(self, file_path: Path | str) -> str:
        """
        Computes the SHA-256 hash of a specified file.
        Reads the file in binary chunks to efficiently handle large files without
        loading the entire content into memory.
        Args:
            file_path (Path | str): The path to the file to be hashed.
        Returns:
            str: The hexadecimal representation of the SHA-256 hash.
        Raises:
            FileNotFoundError: If the provided path does not exist or is not a file.
        """

        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def compute_time_hash(self) -> str:
        """
        Generate a short deterministic "time hash" derived from the current UTC time.
        This function:
        - Reads the current time in UTC (precision: seconds).
        - Formats it as an ISO 8601 timestamp in the form YYYY-MM-DDTHH:MM:SSZ.
        - Computes the SHA-256 digest of that timestamp string.
        - Returns the first 12 hexadecimal characters of the digest (lowercase).
        Returns:
            str: A 12-character lowercase hexadecimal string (48 bits) representing the
                leading portion of the SHA-256 digest of the current UTC timestamp,
                suitable as a concise human-readable batch identifier.

        Behavior and caveats:
        - Determinism: Two calls made within the same UTC second will return the same
        value because the timestamp input is second-granular.
        - Uniqueness and security: This is not a cryptographically secure unique ID.
        The returned 48 bits have a non-zero collision probability and should not be
        relied upon for security-sensitive uniqueness requirements.
        - Clock dependency: Results depend on the system clock being accurate and set
        to UTC; for consistent results across systems, ensure clock synchronization
        (e.g., via NTP).
        Considerations:
        - If you need sub-second uniqueness or stronger collision resistance, include
        additional entropy (e.g., a random salt) or use a UUID/secure RNG approach.
        """

        # Get current UTC time, explicitly
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # The rest of the conversion is identical
        full_hash = hashlib.sha256(timestamp.encode("utf-8")).hexdigest()
        return full_hash[:12]
