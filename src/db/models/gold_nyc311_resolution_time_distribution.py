from sqlalchemy import Column, Date, String, Integer, PrimaryKeyConstraint

from src.db.models import Base


class NYC311ResolutionTimeDistribution(Base):
    __tablename__ = "gold_nyc311_resolution_time_distribution"

    request_month = Column(Date, nullable=False)
    agency = Column(String, nullable=False)
    complaint_type = Column(String, nullable=False)
    resolution_bucket = Column(String, nullable=False)
    request_count = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "request_month",
            "agency",
            "complaint_type",
            "resolution_bucket",
            name="pk_gold_nyc311_month_agency_complaint_bucket",
        ),
    )
