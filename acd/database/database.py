from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acd.config import DATABASE_FILE

DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)