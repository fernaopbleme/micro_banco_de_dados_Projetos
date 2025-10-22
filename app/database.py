# app/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator

SQLALCHEMY_DATABASE_URL = "sqlite:///./project.db"  # arquivo project.db na raiz

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # necessário p/ SQLite + threads do Uvicorn
)

# Habilita FKs no SQLite (senão ON DELETE CASCADE não funciona)
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()

# Fábrica de sessões
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base para os modelos ORM
class Base(DeclarativeBase):
    pass

# Dependency de sessão para FastAPI
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
