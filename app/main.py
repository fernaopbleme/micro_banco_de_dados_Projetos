# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ← importa
from sqlalchemy import text

from .database import engine, Base
from .routers import projetos, tags

Base.metadata.create_all(bind=engine)
with engine.begin() as conn:
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
                role VARCHAR(60),
                UNIQUE (project_id, collaborator_email),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE project_members ADD COLUMN contributed_skill_name VARCHAR(80)"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE project_members ADD COLUMN contributed_skill_level VARCHAR(20)"))
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE project_members DROP COLUMN role"))
    except Exception:
        pass
    conn.execute(text("""
                      UPDATE project_members
                      SET contributed_skill_name = COALESCE(contributed_skill_name, '')
                      """))
    conn.execute(text("""
                      UPDATE project_members
                      SET contributed_skill_level = COALESCE(contributed_skill_level, 'beginner')
                      """))
app = FastAPI(title="Projetos (SQLite)", version="1.0.0")

# === CORS (modo didático para desenvolvimento) ===
# Coloque aqui os endereços de onde você abre o front:
# - se você abre o index.html via um server simples: http://localhost:5500
# - se usa Vite: http://localhost:5173
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # quem pode chamar a API
    allow_credentials=True,
    allow_methods=["*"],        # GET, POST, etc.
    allow_headers=["*"],        # Content-Type, Authorization, etc.
)

# suas rotas
app.include_router(tags.router)
app.include_router(projetos.router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
