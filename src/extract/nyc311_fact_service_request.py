from sqlalchemy import select

from src.db.models import NYC311ServiceRequest
from src.db.session import get_db_session


def get_latest_created_date():
    with get_db_session() as session:
        stmt = select(NYC311ServiceRequest.created_date) \
            .order_by(NYC311ServiceRequest.created_date.desc()) \
            .limit(1)

        return session.execute(stmt).scalar_one_or_none()
