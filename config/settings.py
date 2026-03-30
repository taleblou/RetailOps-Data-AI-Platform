# Project:      RetailOps Data & AI Platform
# Module:       config
# File:         settings.py
# Path:         config/settings.py
#
# Summary:      Defines runtime configuration for the settings layer.
# Purpose:      Provides typed settings and configuration defaults for settings code paths.
# Scope:        config
# Status:       stable
#
# Author(s):    Morteza Taleblou
# Website:      https://taleblou.ir/
# Repository:   https://github.com/taleblou/RetailOps-Data-AI-Platform
#
# License:      Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
# Copyright:    (c) 2025 Morteza Taleblou
#
# Notes:
#   - Main types: Settings
#   - Key APIs: get_settings
#   - Dependencies: functools, pydantic_settings
#   - Constraints: Configuration values must remain consistent with repository
#     environment and deployment defaults.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    api_port: int = 8000
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "retailops"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_database_url(self) -> str | None:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
