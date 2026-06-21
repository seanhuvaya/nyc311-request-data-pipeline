from typing import Optional

from pydantic import BaseModel


class BoroughStat(BaseModel):
    borough: str
    total_count: int
    closed_count: int
    open_count: int
    pct_closed: float
    avg_resolution_hours: Optional[float]
    median_resolution_hours: Optional[float]
