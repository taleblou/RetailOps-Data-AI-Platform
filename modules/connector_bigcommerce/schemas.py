from pydantic import BaseModel, Field


class BigCommerceConnectorConfig(BaseModel):
    store_hash: str
    access_token: str
    resource: str = "orders"
    api_version: str = "v3"
    page_size: int = Field(default=50, ge=1, le=250)
    api_root: str = "https://api.bigcommerce.com/stores"
