from pathlib import Path
from ..config.pkg_config import PkgConfig
from ..util import sha


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

        return sha.compute_file_sha256(file_path=file_path)

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
        return sha.compute_time_hash()
