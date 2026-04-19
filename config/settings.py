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
#   - Dependencies: functools, pydantic_settings, core.ingestion.base.models
#   - Constraints: Configuration values must remain consistent with repository
#     environment and deployment defaults.
#   - Compatibility: Python 3.12+ with repository configuration dependencies.

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.ingestion.base.models import SourceType


class Settings(BaseSettings):
    app_env: str = "dev"
    app_profile: str = "lite"
    api_port: int = 8000
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "retailops"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    enabled_connectors: str = SourceType.CSV.value
    enabled_optional_extras: str = "reporting"

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

    @property
    def enabled_connector_types(self) -> list[SourceType]:
        seen: set[SourceType] = set()
        resolved: list[SourceType] = []
        for raw_value in self.enabled_connectors.split(","):
            normalized = raw_value.strip().lower()
            if not normalized:
                continue
            try:
                source_type = SourceType(normalized)
            except ValueError:
                continue
            if source_type in seen:
                continue
            seen.add(source_type)
            resolved.append(source_type)
        if not resolved:
            return [SourceType.CSV]
        return resolved

    @property
    def enabled_connector_values(self) -> list[str]:
        return [item.value for item in self.enabled_connector_types]

    @property
    def enabled_optional_extra_values(self) -> list[str]:
        allowed = {"reporting", "feature-store", "advanced-serving"}
        seen: set[str] = set()
        resolved: list[str] = []
        for raw_value in self.enabled_optional_extras.split(","):
            normalized = raw_value.strip().lower()
            if not normalized or normalized not in allowed or normalized in seen:
                continue
            seen.add(normalized)
            resolved.append(normalized)
        return resolved


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
