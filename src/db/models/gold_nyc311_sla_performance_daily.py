from sqlalchemy import Column, Date, String, Integer, Float, PrimaryKeyConstraint

from src.db.models import Base


class NYC311SLAPerformanceDaily(Base):
    __tablename__ = "gold_nyc311_sla_performance_daily"

    request_date = Column(Date, nullable=False)
    agency = Column(String, nullable=False)
    complaint_type = Column(String, nullable=False)
    total_closed_requests = Column(Integer, nullable=False)
    closed_within_24h = Column(Integer, nullable=False)
    closed_within_72h = Column(Integer, nullable=False)
    closed_after_72h = Column(Integer, nullable=False)
    pct_closed_within_24h = Column(Float, nullable=False)
    pct_closed_within_72h = Column(Float, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "request_date",
            "agency",
            "complaint_type",
            name="pk_gold_nyc311_request_date_agency_complaint",
        ),
    )
