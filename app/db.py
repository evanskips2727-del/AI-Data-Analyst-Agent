import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

_here = os.path.dirname(os.path.abspath(__file__))
_default_sqlite = "sqlite:///" + os.path.join(os.path.dirname(_here), "data", "app.db")

DATABASE_URL = os.environ.get("DATABASE_URL") or _default_sqlite

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
