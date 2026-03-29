from pydantic import BaseModel, Field


class AdobeCommerceConnectorConfig(BaseModel):
    base_url: str
    access_token: str
    resource: str = "orders"
    store_code: str = "default"
    page_size: int = Field(default=50, ge=1, le=200)
    search_criteria: dict[str, str | int | float] = Field(default_factory=dict)
