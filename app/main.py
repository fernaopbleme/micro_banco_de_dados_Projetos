# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine, Base
from .routers import projetos, tags

app = FastAPI(title="Projetos API", version="1.0.0")

# CORS (didático)
origins = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5500", "http://127.0.0.1:5500"
    "bdprojetos.azurewebsites.net",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Cria/atualiza o schema via SQLAlchemy
    Base.metadata.create_all(bind=engine)

    # Migrações mínimas compatíveis por dialeto
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            try:
                conn.execute(text("ALTER TABLE projects ADD COLUMN category TEXT NOT NULL DEFAULT ''"))
            except Exception:
                pass  # coluna já existe

            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS project_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        collaborator_email VARCHAR(200) NOT NULL,
                        UNIQUE (project_id, collaborator_email),
                        contributed_skill_name VARCHAR(80) DEFAULT '',
                        contributed_skill_level VARCHAR(20) DEFAULT 'beginner',
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                    )
                """))
            except Exception:
                pass

        else:
            # Postgres
            conn.execute(text(
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT ''"
            ))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_members (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    collaborator_email VARCHAR(200) NOT NULL,
                    contributed_skill_name VARCHAR(80) DEFAULT '',
                    contributed_skill_level VARCHAR(20) DEFAULT 'beginner',
                    CONSTRAINT uq_proj_email UNIQUE (project_id, collaborator_email)
                )
            """))

# Rotas
app.include_router(tags.router)
app.include_router(projetos.router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
