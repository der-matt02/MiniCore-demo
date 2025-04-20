from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = "sqlite:///./MiniCore.db"
engine = create_engine(URL_DATABASE, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """
    Function to get a database session.

    Returns:
        Session: The database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

Base = declarative_base()
