# app/routers/tags.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/tags", tags=["tags"])
@router.post("/", response_model=schemas.TagRead, status_code=201)
def create_tag(payload: schemas.TagCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(models.Tag).where(models.Tag.name == payload.name))
    if exists:
        raise HTTPException(status_code=409, detail="Tag name already exists")
    tag = models.Tag(name=payload.name, description=payload.description)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@router.get("/", response_model=list[schemas.TagRead])
def list_tags(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(models.Tag)
    if q:
        stmt = stmt.where(models.Tag.name.like(f"%{q}%"))
    return list(db.scalars(stmt.order_by(models.Tag.name)).all())