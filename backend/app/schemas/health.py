"""Health endpoint contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

HealthStatus = Literal["healthy", "degraded", "unhealthy"]
ComponentStatus = Literal["ok", "degraded", "unavailable"]


class ComponentHealth(BaseModel):
    status: ComponentStatus
    message: str = Field(description="Short, non-sensitive description of the check result.")


class HealthResponse(BaseModel):
    status: HealthStatus = Field(
        description="healthy: all checks passed. degraded: reachable but incomplete. "
        "unhealthy: a required dependency is unavailable."
    )
    message: str
    app_name: str
    version: str
    environment: str
    checked_at: datetime
    components: dict[str, ComponentHealth]
