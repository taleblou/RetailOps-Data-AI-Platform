from pydantic import BaseModel, Field


class PrestaShopConnectorConfig(BaseModel):
    base_url: str
    api_key: str
    resource: str = "orders"
    page_size: int = Field(default=25, ge=1, le=100)
    display: str = "full"
