from __future__ import annotations

from pydantic import BaseModel, Field


class EasyCsvPreviewResponse(BaseModel):
    upload_id: str
    filename: str
    stored_path: str
    delimiter: str = ","
    encoding: str = "utf-8"
    columns: list[str] = Field(default_factory=list)
    sample_rows: list[dict[str, str | None]] = Field(default_factory=list)
    preview_row_count: int = 0
