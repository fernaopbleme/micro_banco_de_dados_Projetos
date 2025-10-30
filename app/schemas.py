# app/schemas.py
from pydantic import BaseModel, Field, conint, EmailStr
from typing import Optional, List, Literal
LEVEL = Literal["beginner", "intermediate", "advanced"]
#MEMBROS
class ProjectMemberAdd(BaseModel):
    collaborator_email: EmailStr
    contributed_skill_name: str
    contributed_skill_level: LEVEL

class ProjectMemberRead(BaseModel):
    id: int
    collaborator_email: EmailStr
    contributed_skill_name: str
    contributed_skill_level: LEVEL
    class Config:
        orm_mode = True
# TAGS
class TagBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: int
    class Config:
        from_attributes = True

# LIGAÇÃO PROJETO↔TAG
class ProjectTagLink(BaseModel):
    tag_id: int
    skill_level: LEVEL

class ProjectTagRead(BaseModel):            # <= mantém o nome ORIGINAL
    id: int
    tag_id: int
    name: str
    skill_level: LEVEL
    class Config:
        orm_mode = True


# PROJETOS
class ProjectBase(BaseModel):
    title: str
    description: str
    category: str


class ProjectCreate(ProjectBase):
    tags: List[ProjectTagLink] = []


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    tags: List[ProjectTagRead] = []
    members: List[ProjectMemberRead] = []   # ← NOVO campo de saída
    class Config:
        orm_mode = True