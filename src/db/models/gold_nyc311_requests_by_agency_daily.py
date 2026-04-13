from sqlalchemy import Column, Date, String, Integer, Float, PrimaryKeyConstraint

from src.db.models import Base


class NYC311RequestsByAgencyDaily(Base):
    __tablename__ = "gold_nyc311_requests_by_agency_daily"

    request_date = Column(Date, nullable=False)
    agency = Column(String, nullable=False)
    total_requests = Column(Integer, nullable=False)
    open_requests = Column(Integer, nullable=False)
    closed_requests = Column(Integer, nullable=False)
    avg_resolution_time_in_hours = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("request_date", "agency", name="pk_gold_nyc311_request_date_agency"),
    )
