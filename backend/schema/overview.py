from datetime import date
from typing import Optional

from pydantic import BaseModel


class WeeklySummaryResponse(BaseModel):
    week_start: date
    week_closed_requests: int
    week_total_requests: int
    week_closed_requests_pct: float
    week_avg_resolution_time_in_hours: float
    prev_week_total_requests: int
    prev_week_total_closed_requests: int
    prev_week_change_in_requests_pct: Optional[float]
    prev_week_change_in_closed_requests_pct: Optional[float]
    prev_week_avg_resolution_time_in_hours: float
    prev_week_avg_resolution_time_in_hours_pct: Optional[float]


class DailySummaryResponse(BaseModel):
    request_date: date
    closed_count: int
    open_count: int
    total_count: int
    avg_resolution_time_in_hours: float
    median_resolution_time_in_hours: float
    pct_closure_daily: float

