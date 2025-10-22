# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ← importa

from .database import engine, Base
from .routers import projetos, tags

Base.metadata.create_all(bind=engine)

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
