"""File validation: extension, real type, size. Never trust filename alone."""
import io, zipfile

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def validate_file_size(size_bytes: int, max_mb: int = 10) -> None:
    if size_bytes > max_mb * 1024 * 1024:
        raise ValueError(f"File too large. Max {max_mb} MB")

def is_real_excel(file_bytes: bytes, filename: str) -> bool:
    """Check magic bytes, not just extension."""
    if filename.lower().endswith(".xlsx"):
        return file_bytes[:2] == b"PK" and zipfile.is_zipfile(io.BytesIO(file_bytes))
    if filename.lower().endswith(".xls"):
        return file_bytes[:4] == b"\xd0\xcf\x11\xe0"
    return False