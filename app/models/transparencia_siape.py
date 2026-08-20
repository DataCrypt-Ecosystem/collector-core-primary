from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from .utils import utcnow


class TransparenciaSiapeServidorOrgaoRaw(Base):
    __tablename__ = "transparencia_siape_servidor_orgao_raw"
    __table_args__ = {"schema": "datacrypt"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_orgao_exercicio_siape: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="")
    nome_orgao_exercicio_siape: Mapped[str] = mapped_column(Text, nullable=False, default="")
    codigo_orgao_superior_exercicio_siape: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        default="",
    )
    nome_orgao_superior_exercicio_siape: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sk_situacao: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    desc_situacao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sk_tipo_vinculo: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    desc_tipo_vinculo: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sk_tipo_servidor: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    desc_tipo_servidor: Mapped[str] = mapped_column(Text, nullable=False, default="")
    licenca: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    pagina_origem: Mapped[int] = mapped_column(Integer, nullable=False)
    filtro_orgao_lotacao: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="")
    filtro_orgao_exercicio: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="")
    filtro_tipo_servidor: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    filtro_tipo_vinculo: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    filtro_licenca: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    payload_original_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class FatoSiapeServidorOrgao(Base):
    __tablename__ = "fato_siape_servidor_orgao"
    __table_args__ = (
        UniqueConstraint(
            "codigo_orgao_exercicio_siape",
            "codigo_orgao_superior_exercicio_siape",
            "sk_situacao",
            "sk_tipo_vinculo",
            "sk_tipo_servidor",
            "licenca",
            name="uq_fato_siape_servidor_orgao_logical",
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_orgao_exercicio_siape: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="")
    nome_orgao_exercicio_siape: Mapped[str] = mapped_column(Text, nullable=False, default="")
    codigo_orgao_superior_exercicio_siape: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        default="",
    )
    nome_orgao_superior_exercicio_siape: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sk_situacao: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    desc_situacao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sk_tipo_vinculo: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    desc_tipo_vinculo: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sk_tipo_servidor: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    desc_tipo_servidor: Mapped[str] = mapped_column(Text, nullable=False, default="")
    licenca: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=0)
    quantidade_pessoas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantidade_vinculos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class TransparenciaSiapeCargaJob(Base):
    __tablename__ = "transparencia_siape_carga_job"
    __table_args__ = (
        UniqueConstraint("job_code", name="uq_transparencia_siape_carga_job_code"),
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
    items: Mapped[list["TransparenciaSiapeCargaJobItem"]] = relationship(
        "TransparenciaSiapeCargaJobItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class TransparenciaSiapeCargaJobItem(Base):
    __tablename__ = "transparencia_siape_carga_job_item"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "filter_type",
            "filter_value",
            name="uq_transparencia_siape_carga_job_item_logical",
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datacrypt.transparencia_siape_carga_job.id"),
        nullable=False,
        index=True,
    )
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
    job: Mapped["TransparenciaSiapeCargaJob"] = relationship(
        "TransparenciaSiapeCargaJob",
        back_populates="items",
    )
