from pydantic import BaseModel


class ShopifyConnectorConfig(BaseModel):
    store_url: str
    access_token: str
    api_version: str = "2024-01"
    resource: str = "orders"
