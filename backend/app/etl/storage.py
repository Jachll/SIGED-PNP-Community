import re
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.etl.tabular import TabularValidationError

SUPPORTED_FILE_SUFFIXES = {".csv", ".xlsx"}
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def persist_local_input_file(input_path: Path, upload_dir: Path = UPLOAD_DIR) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    stored_path = build_managed_path(input_path.name, upload_dir=upload_dir)
    shutil.copy2(input_path, stored_path)
    ensure_non_empty_file(stored_path)
    return stored_path


def store_upload_file(upload: UploadFile, upload_dir: Path = UPLOAD_DIR) -> Path:
    stored_path = build_managed_path(upload.filename or "carga.csv", upload_dir=upload_dir)

    with stored_path.open("wb") as handle:
        shutil.copyfileobj(upload.file, handle)

    ensure_non_empty_file(stored_path)
    if hasattr(upload.file, "seek"):
        upload.file.seek(0)
    return stored_path


def build_managed_path(filename: str, upload_dir: Path = UPLOAD_DIR) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = ensure_supported_suffix(filename)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name or f"lote{suffix}")
    stored_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}_{safe_name}"
    return upload_dir / stored_name


def ensure_supported_suffix(filename: str) -> str:
    suffix = Path((filename or "").strip()).suffix.lower()
    if suffix not in SUPPORTED_FILE_SUFFIXES:
        raise TabularValidationError("Formato no soportado. Usa un archivo .csv o .xlsx.")
    return suffix


def ensure_non_empty_file(file_path: Path) -> None:
    if file_path.stat().st_size > 0:
        return

    file_path.unlink(missing_ok=True)
    raise TabularValidationError("El archivo cargado esta vacio.")
