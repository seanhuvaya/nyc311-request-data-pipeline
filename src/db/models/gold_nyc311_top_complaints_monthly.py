from sqlalchemy import Column, Date, String, Integer, PrimaryKeyConstraint

from src.db.models import Base


class NYC311TopComplaintsMonthly(Base):
    __tablename__ = "gold_nyc311_top_complaints_monthly"

    month = Column(Date, nullable=False)
    borough = Column(String, nullable=False)
    complaint_type = Column(String, nullable=False)
    request_count = Column(Integer, nullable=False)
    rank_in_borough = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "month",
            "borough",
            "complaint_type",
            name="pk_gold_nyc311_month_borough_complaint",
        ),
    )
