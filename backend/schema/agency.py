from typing import Optional

from pydantic import BaseModel


class AgencyStat(BaseModel):
    agency_code: str
    total_count: int
    closed_count: int
    open_backlog: int
    pct_closed: float
    avg_resolution_hours: Optional[float]
    p90_resolution_hours: Optional[float]
