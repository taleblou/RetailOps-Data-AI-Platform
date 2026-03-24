from pydantic import BaseModel, Field


class CsvConnectorConfig(BaseModel):
    file_path: str
    delimiter: str = Field(default=",", min_length=1, max_length=1)
    encoding: str = "utf-8"
    has_header: bool = True
