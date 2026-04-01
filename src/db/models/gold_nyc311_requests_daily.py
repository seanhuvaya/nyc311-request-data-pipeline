from sqlalchemy import Column, DateTime, Integer, Float

from src.db.models import Base


class NYC311RequestsDaily(Base):
    __tablename__ = "gold_nyc311_requests_daily"

    request_date = Column(DateTime(timezone=True), primary_key=True)
    total_requests = Column(Integer, nullable=False)
    open_requests = Column(Integer, nullable=False)
    closed_requests = Column(Integer, nullable=False)
    pct_closed = Column(Float, nullable=False)
    avg_resolution_time_in_minutes = Column(Float, nullable=False)