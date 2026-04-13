from sqlalchemy import Integer, Column, String, Float, DateTime, Boolean

from src.db.models import Base


class NYC311GoldRequestFact(Base):
    __tablename__ = "gold_nyc311_request_fact"

    unique_key = Column(Integer, nullable=False, primary_key=True)
    created_date = Column(DateTime(timezone=True), nullable=False)
    closed_date = Column(DateTime(timezone=True))
    is_closed = Column(Boolean, nullable=False, default=False)
    resolution_time_in_hours = Column(Float)
    agency = Column(String, nullable=False)
    complaint_type = Column(String, nullable=False)
    descriptor = Column(String, nullable=False)
    incident_zip = Column(String, nullable=False)
    borough = Column(String, nullable=False)
    community_board = Column(String, nullable=False)
    council_district = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_type = Column(String, nullable=False)
