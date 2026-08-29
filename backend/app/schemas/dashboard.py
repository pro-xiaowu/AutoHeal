from typing import Any

from pydantic import BaseModel


class DashboardOverview(BaseModel):
    setup_completed: bool
    llm_mode: str
    llm_model: str
    dependencies: dict[str, Any]
