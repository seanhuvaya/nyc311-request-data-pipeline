from sqlalchemy import Column, Date, String, Integer, Float, PrimaryKeyConstraint

from src.db.models import Base


class NYC311OpenBacklogDaily(Base):
    __tablename__ = "gold_nyc311_open_backlog_daily"

    snapshot_date = Column(Date, nullable=False)
    agency = Column(String, nullable=False)
    borough = Column(String, nullable=False)
    complaint_type = Column(String, nullable=False)
    open_backlog_count = Column(Integer, nullable=False)
    avg_age_open_hours = Column(Float)
    max_age_open_hours = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint(
            "snapshot_date",
            "agency",
            "borough",
            "complaint_type",
            name="pk_gold_nyc311_snapshot_agency_borough_complaint",
        ),
    )
