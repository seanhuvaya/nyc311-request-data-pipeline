from typing import Optional

from pydantic import BaseModel


class ComplaintTypeStat(BaseModel):
    complaint_type: str
    total_count: int
    closed_count: int
    pct_closed: float
    avg_resolution_hours: Optional[float]
    median_resolution_hours: Optional[float]
    p90_resolution_hours: Optional[float]
