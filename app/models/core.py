from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Regiao(Base):
    __tablename__ = "dim_regioes"
    __table_args__ = {"schema": "datacrypt"}

    id_regiao: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    estados: Mapped[list[Estado]] = relationship("Estado", back_populates="regiao")

class Estado(Base):
    __tablename__ = "dim_estados"
    __table_args__ = {"schema": "datacrypt"}

    id_estado: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    sigla: Mapped[str] = mapped_column(String(2), nullable=False)
    id_regiao: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datacrypt.dim_regioes.id_regiao"),
        nullable=False,
    )
    regiao: Mapped[Regiao] = relationship("Regiao", back_populates="estados")
    municipios: Mapped[list[Municipio]] = relationship("Municipio", back_populates="estado")

class Municipio(Base):
    __tablename__ = "dim_municipios"
    __table_args__ = {"schema": "datacrypt"}

    id_municipio: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    id_estado: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datacrypt.dim_estados.id_estado"),
        nullable=False,
    )
    estado: Mapped[Estado] = relationship("Estado", back_populates="municipios")
