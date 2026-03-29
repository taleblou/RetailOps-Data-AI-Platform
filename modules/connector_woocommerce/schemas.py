from pydantic import BaseModel, Field


class WooCommerceConnectorConfig(BaseModel):
    store_url: str
    consumer_key: str
    consumer_secret: str
    resource: str = "orders"
    api_version: str = "wc/v3"
    verify_ssl: bool = True
    default_status: str | None = None
    page_size: int = Field(default=50, ge=1, le=100)
