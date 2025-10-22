# app/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/projects", tags=["projects"])
# helper p/ montar resposta com tags

def _project_out(db: Session, project: models.Project) -> schemas.ProjectRead:
    stmt = (
        select(models.ProjectTag, models.Tag)
        .join(models.Tag, models.ProjectTag.tag_id == models.Tag.id)
        .where(models.ProjectTag.project_id == project.id)
        .order_by(models.Tag.name)
    )
    rows = db.execute(stmt).all()
    tags = [
        schemas.ProjectTagRead(
            id=pt.id,
            tag_id=t.id,
            name=t.name,
            description=t.description,
            skill_level=pt.skill_level,
        )
        for pt, t in rows
    ]
    return schemas.ProjectRead(id=project.id, title=project.title, description=project.description, tags=tags)

@router.post("/", response_model=schemas.ProjectRead, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    proj = models.Project(title=payload.title, description=payload.description)
    db.add(proj)
    db.flush()  # garante proj.id

    if payload.tags:
        for link in payload.tags:
            tag = db.get(models.Tag, link.tag_id)
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag not found: {link.tag_id}")
            assoc = models.ProjectTag(project_id=proj.id, tag_id=link.tag_id, skill_level=link.skill_level)
            db.add(assoc)
    db.commit()
    db.refresh(proj)
    return _project_out(db, proj)

@router.get("/", response_model=list[schemas.ProjectRead])
def list_projects(
    q: str | None = Query(default=None, description="search in title/description"),
    tag: str | None = Query(default=None, description="filter by tag name"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(models.Project)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((models.Project.title.like(like)) | (models.Project.description.like(like)))

    if tag:
        sub = (
            select(models.ProjectTag.project_id)
            .join(models.Tag, models.ProjectTag.tag_id == models.Tag.id)
            .where(models.Tag.name == tag)
        )
        stmt = stmt.where(models.Project.id.in_(sub))

    stmt = stmt.order_by(models.Project.created_at.desc()).limit(limit).offset(offset)
    projects = list(db.scalars(stmt).all())
    return [_project_out(db, p) for p in projects]

@router.get("/{project_id}", response_model=schemas.ProjectRead)
def get_project(project_id: int = Path(...), db: Session = Depends(get_db)):
    proj = db.get(models.Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_out(db, proj)

@router.patch("/{project_id}", response_model=schemas.ProjectRead)
def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    proj = db.get(models.Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.title is not None:
        proj.title = payload.title
    if payload.description is not None:
        proj.description = payload.description
    db.commit()
    db.refresh(proj)
    return _project_out(db, proj)

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    proj = db.get(models.Project, project_id)
    if not proj:
        return
    db.delete(proj)
    db.commit()

@router.post("/{project_id}/tags", response_model=schemas.ProjectRead)
def add_tag(project_id: int, link: schemas.ProjectTagLink, db: Session = Depends(get_db)):
    proj = db.get(models.Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    tag = db.get(models.Tag, link.tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # verifica duplicidade
    exists_stmt = select(models.ProjectTag).where(
        (models.ProjectTag.project_id == project_id) & (models.ProjectTag.tag_id == link.tag_id)
    )
    exists = db.scalar(exists_stmt)
    if exists:
        exists.skill_level = link.skill_level
    else:
        db.add(models.ProjectTag(project_id=project_id, tag_id=link.tag_id, skill_level=link.skill_level))
    db.commit()
    return _project_out(db, proj)

@router.delete("/{project_id}/tags/{tag_id}", response_model=schemas.ProjectRead)
def remove_tag(project_id: int, tag_id: int, db: Session = Depends(get_db)):
    proj = db.get(models.Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    assoc = db.scalar(
        select(models.ProjectTag).where(
            (models.ProjectTag.project_id == project_id) & (models.ProjectTag.tag_id == tag_id)
        )
    )
    if assoc:
        db.delete(assoc)
        db.commit()
    return _project_out(db, proj)