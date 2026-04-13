from sqlalchemy import Column, String

from src.db.models import Base


class DimAgency(Base):
    __tablename__ = "dim_agency"

    agency = Column(String, primary_key=True)
