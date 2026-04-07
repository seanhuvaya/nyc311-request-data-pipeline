from sqlalchemy import select

from src.db.models import NYC311ServiceRequest, NYC311RequestsDaily
from src.db.models import NYC311RequestsByComplaintDaily
from src.db.session import get_db_session


def get_requests_by_complaint_type():
    with get_db_session() as session:
        stmt = select(NYC311RequestsByComplaintDaily)

        return session.execute(stmt).scalars().all()


def get_requests():
    with get_db_session() as session:
        stmt = select(NYC311ServiceRequest)

        return session.execute(stmt).scalars().all()


def get_requests_daily():
    with get_db_session() as session:
        stmt = select(NYC311RequestsDaily)

        return session.execute(stmt).scalars().all()
