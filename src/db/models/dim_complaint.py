from sqlalchemy import Column, String, PrimaryKeyConstraint

from src.db.models import Base


class DimComplaint(Base):
    __tablename__ = "dim_complaint"

    complaint_type = Column(String, nullable=False)
    descriptor = Column(String, nullable=False)
    location_type = Column(String, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "complaint_type",
            "descriptor",
            "location_type",
            name="pk_dim_complaint_type_descriptor_location",
        ),
    )
