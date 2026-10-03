"""Deterministic ZIP archive packaging and SHA256 checksum calculation."""

import hashlib
import stat
import zipfile
from pathlib import Path

# Fixed timestamp: 2026-01-01 00:00:00 UTC for reproducible zip builds
FIXED_ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
FIXED_FILE_MODE = 0o644
FIXED_DIR_MODE = 0o755


def create_deterministic_zip(source_dir: Path, output_zip_path: Path) -> tuple[Path, str]:
    """Package source_dir into a deterministic, reproducible ZIP archive.

    Files are stored in alphabetical order with normalized fixed timestamps (2026-01-01 00:00:00)
    and standard file permission flags. Returns (output_zip_path, sha256_hex).
    """
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect all files recursively and sort lexicographically
    all_files: list[Path] = []
    for p in source_dir.rglob("*"):
        if p.is_file():
            all_files.append(p)

    all_files.sort(key=lambda p: p.relative_to(source_dir).as_posix())

    with zipfile.ZipFile(
        output_zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zf:
        for file_path in all_files:
            rel_path = file_path.relative_to(source_dir).as_posix()
            data = file_path.read_bytes()

            zinfo = zipfile.ZipInfo(filename=rel_path, date_time=FIXED_ZIP_TIMESTAMP)
            # Set standard permission bits (rw-r--r--)
            zinfo.external_attr = (stat.S_IFREG | FIXED_FILE_MODE) << 16
            zinfo.compress_type = zipfile.ZIP_DEFLATED

            zf.writestr(zinfo, data)

    # Compute sha256 checksum
    hasher = hashlib.sha256()
    with open(output_zip_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    sha256_hex = hasher.hexdigest()
    return output_zip_path, sha256_hex
