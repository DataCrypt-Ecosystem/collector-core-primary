from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

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
