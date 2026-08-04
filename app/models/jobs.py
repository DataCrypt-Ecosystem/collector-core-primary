from __future__ import annotations
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .utils import utcnow

class TransparenciaCargaJob(Base):
    __tablename__ = "transparencia_carga_job"
    __table_args__ = (
        UniqueConstraint("job_code", name="uq_transparencia_carga_job_code"),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_carga: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="pending")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    running_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    items: Mapped[list[TransparenciaCargaJobItem]] = relationship(
        "TransparenciaCargaJobItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )

class TransparenciaCargaJobItem(Base):
    __tablename__ = "transparencia_carga_job_item"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "tipo_beneficio",
            "codigo_ibge",
            "mes_ano",
            name="uq_transparencia_carga_job_item_logical",
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datacrypt.transparencia_carga_job.id"),
        nullable=False,
        index=True,
    )
    tipo_beneficio: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo_ibge: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    mes_ano: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    pages_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    job: Mapped[TransparenciaCargaJob] = relationship("TransparenciaCargaJob", back_populates="items")
