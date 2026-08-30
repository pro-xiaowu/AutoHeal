from typing import Any

from pydantic import BaseModel


class DashboardOverview(BaseModel):
    setup_completed: bool
    llm_provider: str
    llm_api_format: str
    llm_migration_required: bool = False
    llm_model: str
    dependencies: dict[str, Any]
