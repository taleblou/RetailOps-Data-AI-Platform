from pydantic import BaseModel, Field


class DatabaseConnectorConfig(BaseModel):
    database_url: str
    query: str
    sample_limit: int = Field(default=5, ge=1, le=100)
