from sqlalchemy import Column, Date, Integer, String, Boolean

from src.db.models import Base


class DimDate(Base):
    __tablename__ = "dim_date"

    date = Column(Date, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String, nullable=False)
    week = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, nullable=False)
