"""Streaming file download with SHA-256 verification."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

from ghidractl.errors import ChecksumMismatchError, DownloadError

ProgressCallback = Callable[[int, int], None]


async def download_file(
    client: Any,
    url: str,
    dest: Path,
    expected_sha256: str | None = None,
    progress_callback: ProgressCallback | None = None,
    chunk_size: int = 65536,
) -> Path:
    """Download a file with streaming and optional SHA-256 verification.

    Args:
        client: An HttpClient instance.
        url: URL to download.
        dest: Destination file path.
        expected_sha256: Expected SHA-256 hex digest (lowercase).
        progress_callback: Called with (bytes_downloaded, total_bytes).
        chunk_size: Size of each read chunk.

    Returns:
        Path to the downloaded file.

    Raises:
        DownloadError: If download fails.
        ChecksumMismatchError: If SHA-256 doesn't match.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    downloaded = 0

    try:
        resp = await client.stream(url)

        try:
            total = int(resp.headers.get("content-length", 0))

            with open(dest, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size):
                    f.write(chunk)
                    sha256.update(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)
        finally:
            await resp.aclose()

    except Exception as exc:
        # Clean up partial download
        if dest.exists():
            dest.unlink()
        if isinstance(exc, (ChecksumMismatchError, DownloadError)):
            raise
        raise DownloadError(f"Download failed: {exc}") from exc

    actual_hash = sha256.hexdigest()
    if expected_sha256 and actual_hash != expected_sha256.lower():
        dest.unlink(missing_ok=True)
        raise ChecksumMismatchError(expected=expected_sha256.lower(), actual=actual_hash)

    return dest
