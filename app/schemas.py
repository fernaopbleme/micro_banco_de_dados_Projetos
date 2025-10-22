# app/schemas.py
from pydantic import BaseModel, Field, conint
from typing import Optional, List, Literal


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

LEVEL = Literal["beginner", "intermediate", "advanced"]

# LIGAÇÃO PROJETO↔TAG
class ProjectTagLink(BaseModel):
    tag_id: int
    skill_level: LEVEL

class ProjectTagRead(BaseModel):
    id: int
    tag_id: int
    name: str
    description: Optional[str]
    skill_level: LEVEL


# PROJETOS
class ProjectBase(BaseModel):
    title: str
    description: str


class ProjectCreate(ProjectBase):
    tags: Optional[List[ProjectTagLink]] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    tags: List[ProjectTagRead]
    class Config:
        from_attributes = True