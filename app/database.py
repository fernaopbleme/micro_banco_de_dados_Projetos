# app/database.py
import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

# Lê a URL do ambiente; se não houver, usa SQLite local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Para SQLite: precisa desse connect_args; para Postgres, fica vazio
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Logs de diagnóstico
print(">> DATABASE_URL efetiva (mascarada):", DATABASE_URL.split("@")[-1])
print(">> Dialect:", engine.dialect.name)

# PRAGMA SOMENTE NO SQLITE (listener escopado ao 'engine')
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def _sqlite_fk_on(dbapi_conn, conn_record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
