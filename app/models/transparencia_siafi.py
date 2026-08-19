from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

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
