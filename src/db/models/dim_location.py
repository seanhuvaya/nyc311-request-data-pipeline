from sqlalchemy import Column, String, PrimaryKeyConstraint

from src.db.models import Base


class DimLocation(Base):
    __tablename__ = "dim_location"

    incident_zip = Column(String, nullable=False)
    borough = Column(String, nullable=False)
    city = Column(String, nullable=False)
    community_board = Column(String, nullable=False)
    council_district = Column(String, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("incident_zip", "borough", name="pk_dim_location_zip_borough"),
    )
