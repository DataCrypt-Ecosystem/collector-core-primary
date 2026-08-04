from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .utils import utcnow

class DimPesquisaIBGE(Base):
    __tablename__ = "dim_pesquisa_ibge"
    __table_args__ = {"schema": "datacrypt"}

    codigo: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    situacao: Mapped[str] = mapped_column(String(50), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=True)
    periodicidade_divulgacao: Mapped[str] = mapped_column(String(50), nullable=True)
    tags_tematicas: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    periodos: Mapped[list["DimPesquisaPeriodo"]] = relationship(
        "DimPesquisaPeriodo",
        back_populates="pesquisa",
        cascade="all, delete-orphan",
    )

class DimPesquisaPeriodo(Base):
    __tablename__ = "dim_pesquisa_periodo"
    __table_args__ = (
        UniqueConstraint("codigo_pesquisa", "ano", "mes", name="uq_dim_pesquisa_periodo"),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_pesquisa: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("datacrypt.dim_pesquisa_ibge.codigo"),
        nullable=False,
        index=True,
    )
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nome_ocorrencia: Mapped[str] = mapped_column(String(200), nullable=True)
    status_processamento: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    
    pesquisa: Mapped[DimPesquisaIBGE] = relationship("DimPesquisaIBGE", back_populates="periodos")

class FatoDemografia(Base):
    __tablename__ = "fato_demografia"
    __table_args__ = (
        UniqueConstraint(
            "codigo_ibge_municipio", "ano", "variavel_codigo", 
            name="uq_fato_demografia"
        ),
        {"schema": "datacrypt"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_ibge_municipio: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    variavel_codigo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    valor_estatistico: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
