from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .utils import utcnow

class TransparenciaOrgaoSiafiRaw(Base):
    __tablename__ = "transparencia_orgao_siafi_raw"
    __table_args__ = {"schema": "datacrypt"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    pagina_origem: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_original_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

class TransparenciaOrgaoSiapeRaw(Base):
    __tablename__ = "transparencia_orgao_siape_raw"
    __table_args__ = {"schema": "datacrypt"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    pagina_origem: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_original_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

class TransparenciaOrgaoSiafi(Base):
    __tablename__ = "transparencia_orgao_siafi"
    __table_args__ = {"schema": "datacrypt"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    status_registro: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    elegivel_dashboard: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

class TransparenciaOrgaoSiape(Base):
    __tablename__ = "transparencia_orgao_siape"
    __table_args__ = {"schema": "datacrypt"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    status_registro: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    elegivel_dashboard: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

class FatoRepasseMunicipio(Base):
    __tablename__ = "fato_repasse_municipio"
    __table_args__ = (
        UniqueConstraint(
            "tipo_beneficio",
            "data_referencia",
            "municipio_codigo_ibge",
            name="uq_fato_repasse_municipio_logical",
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tipo_beneficio: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data_referencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    municipio_codigo_ibge: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    quantidade_beneficiados: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
