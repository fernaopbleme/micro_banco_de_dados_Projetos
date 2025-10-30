from datetime import datetime
from sqlalchemy import (
String, Text, Integer, ForeignKey, CheckConstraint,
DateTime, func, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
from typing import Optional, List, Literal
LEVEL = Literal["beginner", "intermediate", "advanced"]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "collaborator_email", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    collaborator_email: Mapped[str] = mapped_column(String(200))  # ← identificador vindo do outro serviço
    contributed_skill_name: Mapped[str] = mapped_column(String(80))
    contributed_skill_level: Mapped["LEVEL"] = mapped_column()

class Project(Base, TimestampMixin):
    __tablename__ = "projects"


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60))

    members: Mapped[list["ProjectMember"]] = relationship(
        backref="project", cascade="all, delete-orphan")

    tags: Mapped[list["ProjectTag"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
)


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)


    projects: Mapped[list["ProjectTag"]] = relationship(
    back_populates="tag", cascade="all, delete-orphan"
)


class ProjectTag(Base, TimestampMixin):
    __tablename__ = "project_tags"
    __table_args__ = (
        UniqueConstraint("project_id", "tag_id", name="uq_project_tag"),
        # ✅ agora o nível é textual e limitado a 3 opções
        CheckConstraint(
            "skill_level IN ('beginner','intermediate','advanced')",
            name="ck_skill_enum"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    skill_level: Mapped[str] = mapped_column(String(12), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="projects")

