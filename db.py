import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

db_user = os.environ.get('PG_USER', 'postgres')
db_password = os.environ.get('PG_PASSWORD', '')
db_host = os.environ.get('PG_HOST', 'localhost')
db_port = os.environ.get('PG_PORT', '5432')
db_name = os.environ.get('PG_DATABASE', 'postgres')

database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
