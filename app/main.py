
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine, Base
from .routers import projetos, tags

# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import projetos, tags

app = FastAPI(title="Projetos API", version="1.0.0")

# CORS: simples e permissivo (ajuste se precisar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ou liste domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 Sem on_startup / create_all: DDL sai do ciclo de boot.

# Rotas
app.include_router(tags.router)
app.include_router(projetos.router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
