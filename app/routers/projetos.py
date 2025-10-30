# app/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/projects", tags=["projects"])
# helper p/ montar resposta com tags

def _project_out(p: models.Project) -> schemas.ProjectRead:
    return schemas.ProjectRead(
        id=p.id,
        title=p.title,
        description=p.description,
        category=p.category,
        tags=[
            schemas.ProjectTagRead(
                id=t.id,
                tag_id=t.tag_id,
                name=t.tag.name,
                skill_level=t.skill_level
            )
            for t in p.tags
        ],
        members=[
            schemas.ProjectMemberRead(
                id=m.id,
                collaborator_email=m.collaborator_email,
                contributed_skill_name=m.contributed_skill_name,
                contributed_skill_level=m.contributed_skill_level,
            ) for m in p.members
        ]
    )

#MEMBROS:
@router.post("/{project_id}/members", response_model=schemas.ProjectMemberRead, status_code=201)
def add_member(project_id: int, payload: schemas.ProjectMemberAdd, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    exists = db.query(models.ProjectMember).filter_by(
        project_id=project_id,
        collaborator_email=str(payload.collaborator_email)
    ).first()
    if exists:
        raise HTTPException(409, "Collaborator already linked to this project")

    member = models.ProjectMember(
        project_id=project_id,
        collaborator_email=str(payload.collaborator_email),
        contributed_skill_name=payload.contributed_skill_name,
        contributed_skill_level=payload.contributed_skill_level,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    # retorno manual (evita from_orm do Pydantic v2)
    return schemas.ProjectMemberRead(
        id=member.id,
        collaborator_email=member.collaborator_email,
        contributed_skill_name=member.contributed_skill_name,
        contributed_skill_level=member.contributed_skill_level,
    )

@router.get("/{project_id}/members", response_model=list[schemas.ProjectMemberRead])
def list_members(project_id: int, db: Session = Depends(get_db)):
    project = (
        db.query(models.Project)
          .options(joinedload(models.Project.members))
          .filter(models.Project.id == project_id)
          .first()

    )
    if not project:
        raise HTTPException(404, "Project not found")
    return [
        schemas.ProjectMemberRead(
            id=m.id,
            collaborator_email=m.collaborator_email,
            contributed_skill_name=m.contributed_skill_name,
            contributed_skill_level=m.contributed_skill_level,
        )
        for m in project.members
    ]

@router.delete("/{project_id}/members/{email}", status_code=204)
def remove_member(
    project_id: int,
    email: str = Path(..., description="Email do colaborador"),
    db: Session = Depends(get_db)
):
    member = db.query(models.ProjectMember).filter_by(
        project_id=project_id,
        collaborator_email=email
    ).first()
    if not member:
        raise HTTPException(404, "Member not found in this project")
    db.delete(member)
    db.commit()

#PROJETOS:
@router.post("/", response_model=schemas.ProjectRead, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    # cria o projeto (categoria obrigatória)
    project = models.Project(
        title=payload.title,
        description=payload.description,
        category=payload.category,
    )
    db.add(project)
    db.flush()  # mantém seu padrão para ter project.id

    # cria os links de tags (mantendo LEVEL e sua lógica atual)
    for link in payload.tags:  # ProjectTagLink (seu nome original)
        tag = db.query(models.Tag).filter(models.Tag.id == link.tag_id).first()
        if not tag:
            raise HTTPException(status_code=400, detail=f"Tag id={link.tag_id} não existe")
        db.add(models.ProjectTag(
            project_id=project.id,
            tag_id=link.tag_id,
            skill_level=link.skill_level  # LEVEL
        ))

    db.commit()

    # recarrega com join para ter tag.name disponível no _project_out
    project = (
        db.query(models.Project)
          .options(joinedload(models.Project.tags).joinedload(models.ProjectTag.tag))
          .filter(models.Project.id == project.id)
          .first()
    )

    return _project_out(project)

@router.get("/", response_model=list[schemas.ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    q: str | None = None,
    tag: str | None = None,
    category: str | None = None,
    collab_email: str | None = None,   # ← NOVO filtro opcional
):
    qset = (
        db.query(models.Project)
          .options(
              joinedload(models.Project.tags).joinedload(models.ProjectTag.tag),
              joinedload(models.Project.members)
          )
    )
    if q:
        like = f"%{q}%"
        qset = qset.filter(
            (models.Project.title.ilike(like)) |
            (models.Project.description.ilike(like))
        )
    if category:
        qset = qset.filter(models.Project.category.ilike(category))

    projects = qset.all()

    # Filtrar por tag por nome (em memória, como você já fazia)
    if tag:
        projects = [
            p for p in projects
            if any(t.tag.name.lower() == tag.lower() for t in p.tags)
        ]

    # Filtrar por colaborador (em memória, simples)
    if collab_email:
        projects = [
            p for p in projects
            if any(m.collaborator_email.lower() == collab_email.lower() for m in p.members)
        ]

    return [_project_out(p) for p in projects]

@router.get("/{project_id}", response_model=schemas.ProjectRead)
def get_project(project_id: int = Path(...), db: Session = Depends(get_db)):
    proj = db.get(models.Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_out(proj)

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
    return _project_out(proj)

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
    return _project_out( proj)

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
    return _project_out(proj)

@router.get("/{project_id}/required-skills")
def required_skills(project_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Project)\
          .options(joinedload(models.Project.tags).joinedload(models.ProjectTag.tag))\
          .filter(models.Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return [{"name": t.tag.name, "level": t.skill_level} for t in p.tags]


#GET /projects para o postman

#Sem filtros:

# Por termo (título/descrição):
#
# URL: /projects?q=hackathon
#
# Por categoria:
#
# URL: /projects?category=engenharia%20e%20m%C3%BAsica
#
# Por nome da tag:
#
# URL: /projects?tag=React
#
# Combinado:
#
# URL: /projects?q=mvp&category=educa%C3%A7%C3%A3o%20e%20IA&tag=Python