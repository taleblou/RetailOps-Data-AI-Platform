from __future__ import annotations

import csv
import json
import re
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from core.api.schemas.easy_csv import EasyCsvPreviewResponse

router = APIRouter(prefix="/easy-csv", tags=["easy-csv"])

UPLOAD_DIR = Path("data/uploads")
PREVIEW_LIMIT = 10
SUPPORTED_DELIMITERS = ",;\t|"


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
    return cleaned or "upload.csv"


def _metadata_path(upload_id: str) -> Path:
    return UPLOAD_DIR / f"{upload_id}.json"


def _write_metadata(payload: dict[str, Any]) -> None:
    path = _metadata_path(payload["upload_id"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_metadata(upload_id: str) -> dict[str, Any]:
    path = _metadata_path(upload_id)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found.",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=SUPPORTED_DELIMITERS)
    except csv.Error:
        return ","
    return getattr(dialect, "delimiter", ",")


def _build_preview(
    *,
    upload_id: str,
    filename: str,
    stored_path: Path,
    delimiter: str,
    encoding: str,
) -> EasyCsvPreviewResponse:
    with stored_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = reader.fieldnames or []
        sample_rows: list[dict[str, str | None]] = []

        for index, row in enumerate(reader, start=1):
            sample_rows.append({key: value for key, value in row.items()})
            if index >= PREVIEW_LIMIT:
                break

    return EasyCsvPreviewResponse(
        upload_id=upload_id,
        filename=filename,
        stored_path=str(stored_path),
        delimiter=delimiter,
        encoding=encoding,
        columns=columns,
        sample_rows=sample_rows,
        preview_row_count=len(sample_rows),
    )


@router.post("/upload", response_model=EasyCsvPreviewResponse)
async def upload_csv(
    file: Annotated[UploadFile, File(...)],
) -> EasyCsvPreviewResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are supported in this step.",
        )

    _ensure_upload_dir()

    upload_id = uuid.uuid4().hex
    safe_name = _safe_filename(file.filename)
    stored_path = UPLOAD_DIR / f"{upload_id}_{safe_name}"

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        decoded_text = raw_bytes.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only UTF-8 CSV files are supported in this step.",
        ) from exc

    stored_path.write_bytes(raw_bytes)

    sample_text = decoded_text[:4096]
    delimiter = _detect_delimiter(sample_text)

    metadata = {
        "upload_id": upload_id,
        "filename": file.filename,
        "stored_path": str(stored_path),
        "delimiter": delimiter,
        "encoding": encoding,
    }
    _write_metadata(metadata)

    return _build_preview(
        upload_id=upload_id,
        filename=file.filename,
        stored_path=stored_path,
        delimiter=delimiter,
        encoding=encoding,
    )


@router.get("/{upload_id}/preview", response_model=EasyCsvPreviewResponse)
def get_preview(upload_id: str) -> EasyCsvPreviewResponse:
    metadata = _read_metadata(upload_id)
    stored_path = Path(metadata["stored_path"])
    if not stored_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored CSV file not found.",
        )

    return _build_preview(
        upload_id=metadata["upload_id"],
        filename=metadata["filename"],
        stored_path=stored_path,
        delimiter=metadata["delimiter"],
        encoding=metadata["encoding"],
    )
