from sqlalchemy import Column, Date, String, Integer, Float

from src.db.models import Base


class NYC311RequestsByAgencyDaily(Base):
    __tablename__ = "gold_nyc311_requests_by_agency_daily"

    request_date = Column(Date, nullable=False)
    agency = Column(String, nullable=False)
    total_requests = Column(Integer, nullable=False)
    open_requests = Column(Integer, nullable=False)
    closed_requests = Column(Integer, nullable=False)
    avg_resolution_time_in_hours = Column(Float, nullable=False)
