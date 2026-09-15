from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from .utils import utcnow


class TransparenciaSiafiDespesaOrgaoRaw(Base):
    __tablename__ = "transparencia_siafi_despesa_orgao_raw"
    __table_args__ = {"schema": "datacrypt"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    codigo_orgao: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    orgao: Mapped[str] = mapped_column(Text, nullable=False)
    codigo_orgao_superior: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="")
    orgao_superior: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pagina_origem: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_original_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class FatoSiafiDespesaOrgaoAnual(Base):
    __tablename__ = "fato_siafi_despesa_orgao_anual"
    __table_args__ = (
        UniqueConstraint(
            "ano",
            "codigo_orgao",
            "codigo_orgao_superior",
            name="uq_fato_siafi_despesa_orgao_anual_logical",
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    codigo_orgao: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    orgao: Mapped[str] = mapped_column(Text, nullable=False)
    codigo_orgao_superior: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="")
    orgao_superior: Mapped[str] = mapped_column(Text, nullable=False, default="")
    empenhado: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    liquidado: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pago: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class TransparenciaSiafiCargaJob(Base):
    __tablename__ = "transparencia_siafi_carga_job"
    __table_args__ = (
        UniqueConstraint("job_code", name="uq_transparencia_siafi_carga_job_code"),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="pending")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    running_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    items: Mapped[list["TransparenciaSiafiCargaJobItem"]] = relationship(
        "TransparenciaSiafiCargaJobItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class TransparenciaSiafiCargaJobItem(Base):
    __tablename__ = "transparencia_siafi_carga_job_item"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "ano",
            "filter_type",
            "filter_value",
            name="uq_transparencia_siafi_carga_job_item_logical",
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datacrypt.transparencia_siafi_carga_job.id"),
        nullable=False,
        index=True,
    )
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    filter_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    filter_value: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    pages_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    facts_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    facts_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    job: Mapped["TransparenciaSiafiCargaJob"] = relationship(
        "TransparenciaSiafiCargaJob",
        back_populates="items",
    )
