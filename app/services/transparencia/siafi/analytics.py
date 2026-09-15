from __future__ import annotations

from decimal import Decimal
from typing import Literal

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.models import FatoSiafiDespesaOrgaoAnual

SiafiIndicador = Literal["empenhado", "liquidado", "pago"]
SiafiOrdem = Literal["asc", "desc"]


def _get_indicator_column(indicador: SiafiIndicador):
    return getattr(FatoSiafiDespesaOrgaoAnual, indicador)


def get_siafi_serie_historica(
    db: Session,
    *,
    codigo_orgao: str,
    codigo_orgao_superior: str | None = None,
):
    query = db.query(FatoSiafiDespesaOrgaoAnual).filter(
        FatoSiafiDespesaOrgaoAnual.codigo_orgao == codigo_orgao
    )

    if codigo_orgao_superior is not None:
        query = query.filter(
            FatoSiafiDespesaOrgaoAnual.codigo_orgao_superior == codigo_orgao_superior
        )

    items = query.order_by(FatoSiafiDespesaOrgaoAnual.ano.asc()).all()
    if not items:
        return {
            "codigo_orgao": codigo_orgao,
            "orgao": None,
            "codigo_orgao_superior": codigo_orgao_superior,
            "orgao_superior": None,
            "data": [],
        }

    first = items[0]
    return {
        "codigo_orgao": codigo_orgao,
        "orgao": first.orgao,
        "codigo_orgao_superior": first.codigo_orgao_superior,
        "orgao_superior": first.orgao_superior,
        "data": [
            {
                "ano": item.ano,
                "empenhado": Decimal(item.empenhado or 0),
                "liquidado": Decimal(item.liquidado or 0),
                "pago": Decimal(item.pago or 0),
            }
            for item in items
        ],
    }


def get_siafi_ranking(
    db: Session,
    *,
    ano: int,
    indicador: SiafiIndicador,
    codigo_orgao_superior: str | None = None,
    limit: int = 10,
    ordem: SiafiOrdem = "desc",
):
    column = _get_indicator_column(indicador)
    query = db.query(
        FatoSiafiDespesaOrgaoAnual.codigo_orgao.label("codigo_orgao"),
        FatoSiafiDespesaOrgaoAnual.orgao.label("orgao"),
        FatoSiafiDespesaOrgaoAnual.codigo_orgao_superior.label("codigo_orgao_superior"),
        FatoSiafiDespesaOrgaoAnual.orgao_superior.label("orgao_superior"),
        column.label("valor"),
    ).filter(FatoSiafiDespesaOrgaoAnual.ano == ano)

    if codigo_orgao_superior is not None:
        query = query.filter(
            FatoSiafiDespesaOrgaoAnual.codigo_orgao_superior == codigo_orgao_superior
        )

    ordering = asc(column) if ordem == "asc" else desc(column)
    items = query.order_by(ordering, FatoSiafiDespesaOrgaoAnual.codigo_orgao.asc()).limit(limit).all()

    return {
        "ano": ano,
        "indicador": indicador,
        "ordem": ordem,
        "codigo_orgao_superior": codigo_orgao_superior,
        "data": [
            {
                "codigo_orgao": item.codigo_orgao,
                "orgao": item.orgao,
                "codigo_orgao_superior": item.codigo_orgao_superior,
                "orgao_superior": item.orgao_superior,
                "valor": Decimal(item.valor or 0),
            }
            for item in items
        ],
    }


def get_siafi_agregacao(
    db: Session,
    *,
    ano: int,
    codigo_orgao_superior: str | None = None,
):
    query = db.query(
        func.count(FatoSiafiDespesaOrgaoAnual.id).label("quantidade_orgaos"),
        func.coalesce(func.sum(FatoSiafiDespesaOrgaoAnual.empenhado), 0).label("total_empenhado"),
        func.coalesce(func.sum(FatoSiafiDespesaOrgaoAnual.liquidado), 0).label("total_liquidado"),
        func.coalesce(func.sum(FatoSiafiDespesaOrgaoAnual.pago), 0).label("total_pago"),
    ).filter(FatoSiafiDespesaOrgaoAnual.ano == ano)

    if codigo_orgao_superior is not None:
        query = query.filter(
            FatoSiafiDespesaOrgaoAnual.codigo_orgao_superior == codigo_orgao_superior
        )

    row = query.one()
    return {
        "ano": ano,
        "codigo_orgao_superior": codigo_orgao_superior,
        "quantidade_orgaos": int(row.quantidade_orgaos or 0),
        "total_empenhado": Decimal(row.total_empenhado or 0),
        "total_liquidado": Decimal(row.total_liquidado or 0),
        "total_pago": Decimal(row.total_pago or 0),
    }


def get_siafi_comparativo(
    db: Session,
    *,
    ano: int,
    codigos_orgao: list[str],
):
    normalized_codes = []
    seen_codes: set[str] = set()
    for raw_code in codigos_orgao:
        code = str(raw_code).strip()
        if not code:
            continue
        if code in seen_codes:
            continue
        seen_codes.add(code)
        normalized_codes.append(code)

    if not normalized_codes:
        raise ValueError("Informe ao menos um codigo de orgao")

    items = (
        db.query(FatoSiafiDespesaOrgaoAnual)
        .filter(
            FatoSiafiDespesaOrgaoAnual.ano == ano,
            FatoSiafiDespesaOrgaoAnual.codigo_orgao.in_(normalized_codes),
        )
        .order_by(FatoSiafiDespesaOrgaoAnual.codigo_orgao.asc())
        .all()
    )

    return {
        "ano": ano,
        "data": [
            {
                "codigo_orgao": item.codigo_orgao,
                "orgao": item.orgao,
                "codigo_orgao_superior": item.codigo_orgao_superior,
                "orgao_superior": item.orgao_superior,
                "empenhado": Decimal(item.empenhado or 0),
                "liquidado": Decimal(item.liquidado or 0),
                "pago": Decimal(item.pago or 0),
            }
            for item in items
        ],
    }
