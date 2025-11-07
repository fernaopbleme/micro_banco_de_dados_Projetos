
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine, Base
from .routers import projetos, tags
app = FastAPI(title="Projetos API", version="1.0.0")

# CORS (liste explicitamente seus fronts)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://bdprojetos.azurewebsites.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],           # inclui Authorization, X-User-Email etc.
)

@app.on_event("startup")
def on_startup():
    # Cria/atualiza o schema via SQLAlchemy
    Base.metadata.create_all(bind=engine)

    # Migrações mínimas compatíveis por dialeto
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            # category
            try:
                conn.execute(text(
                    "ALTER TABLE projects ADD COLUMN category TEXT NOT NULL DEFAULT ''"
                ))
            except Exception:
                pass  # já existe

            # owner_email (agora usando e-mail como dono; banco vazio => simples)
            try:
                conn.execute(text(
                    "ALTER TABLE projects ADD COLUMN owner_email TEXT"
                ))
            except Exception:
                pass  # já existe

            # members (tabela auxiliar)
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
            conn.execute(text(
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_email TEXT"
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

