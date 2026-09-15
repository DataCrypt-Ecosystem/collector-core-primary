from __future__ import annotations
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .utils import utcnow

class DimSiconfiEnte(Base):
    __tablename__ = "dim_siconfi_entes"
    __table_args__ = {"schema": "datacrypt"}

    cod_ibge: Mapped[str] = mapped_column(String(10), primary_key=True, index=True)
    ente: Mapped[str] = mapped_column(String(100), nullable=False)
    capital: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    regiao: Mapped[str] = mapped_column(String(50), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    esfera: Mapped[str] = mapped_column(String(20), nullable=False)
    exercicio: Mapped[int] = mapped_column(Integer, nullable=False)
    populacao: Mapped[int] = mapped_column(Integer, nullable=True)
    cnpj: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
