from typing import Optional

from pydantic import BaseModel


class DayOfWeekStat(BaseModel):
    day_of_week: int
    day_name: str
    total_count: int
    pct_closed: float
    avg_resolution_hours: Optional[float]
