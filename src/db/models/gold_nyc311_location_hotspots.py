from sqlalchemy import Column, String, Integer, Float, PrimaryKeyConstraint

from src.db.models import Base


class NYC311LocationHotspots(Base):
    __tablename__ = "gold_nyc311_location_hotspots"

    borough = Column(String, nullable=False)
    incident_zip = Column(String, nullable=False)
    complaint_type = Column(String, nullable=False)
    request_count = Column(Integer, nullable=False)
    avg_latitude = Column(Float)
    avg_longitude = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint(
            "borough",
            "incident_zip",
            "complaint_type",
            name="pk_gold_nyc311_borough_zip_complaint",
        ),
    )
