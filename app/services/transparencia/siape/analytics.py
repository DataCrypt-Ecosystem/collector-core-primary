from __future__ import annotations

from typing import Literal

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Query, Session

from app.models import FatoSiapeServidorOrgao

SiapeIndicador = Literal["quantidade_pessoas", "quantidade_vinculos"]
SiapeOrdem = Literal["asc", "desc"]
SiapeAgrupamento = Literal["situacao", "tipoVinculo", "tipoServidor", "licenca"]


def _apply_filters(
    query: Query,
    *,
    codigo_orgao_exercicio: str | None = None,
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
):
    if codigo_orgao_exercicio is not None:
        query = query.filter(FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape == codigo_orgao_exercicio)
    if codigo_orgao_superior_exercicio is not None:
        query = query.filter(
            FatoSiapeServidorOrgao.codigo_orgao_superior_exercicio_siape == codigo_orgao_superior_exercicio
        )
    if tipo_servidor is not None:
        query = query.filter(FatoSiapeServidorOrgao.sk_tipo_servidor == tipo_servidor)
    if tipo_vinculo is not None:
        query = query.filter(FatoSiapeServidorOrgao.sk_tipo_vinculo == tipo_vinculo)
    if situacao is not None:
        query = query.filter(FatoSiapeServidorOrgao.sk_situacao == situacao)
    if licenca is not None:
        query = query.filter(FatoSiapeServidorOrgao.licenca == licenca)
    return query


def _resolve_distribution_columns(agrupar_por: SiapeAgrupamento):
    if agrupar_por == "situacao":
        return (
            FatoSiapeServidorOrgao.sk_situacao,
            FatoSiapeServidorOrgao.desc_situacao,
        )
    if agrupar_por == "tipoVinculo":
        return (
            FatoSiapeServidorOrgao.sk_tipo_vinculo,
            FatoSiapeServidorOrgao.desc_tipo_vinculo,
        )
    if agrupar_por == "tipoServidor":
        return (
            FatoSiapeServidorOrgao.sk_tipo_servidor,
            FatoSiapeServidorOrgao.desc_tipo_servidor,
        )
    return (
        FatoSiapeServidorOrgao.licenca,
        None,
    )


def _licenca_description(value: int) -> str:
    return "Com licenca" if value == 1 else "Sem licenca"


def _build_distribution(
    db: Session,
    *,
    agrupar_por: SiapeAgrupamento,
    codigo_orgao_exercicio: str | None = None,
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
):
    key_column, desc_column = _resolve_distribution_columns(agrupar_por)
    query = db.query(
        key_column.label("chave"),
        func.count(func.distinct(FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape)).label("quantidade_orgaos"),
        func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_pessoas), 0).label("quantidade_pessoas"),
        func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_vinculos), 0).label("quantidade_vinculos"),
    )

    if desc_column is not None:
        query = query.add_columns(desc_column.label("descricao"))

    query = _apply_filters(
        query,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )

    group_columns = [key_column]
    if desc_column is not None:
        group_columns.append(desc_column)

    items = query.group_by(*group_columns).order_by(key_column.asc()).all()

    data = []
    for item in items:
        chave = str(item.chave)
        descricao = item.descricao if desc_column is not None else _licenca_description(int(item.chave or 0))
        data.append(
            {
                "chave": chave,
                "descricao": descricao or "",
                "quantidade_orgaos": int(item.quantidade_orgaos or 0),
                "quantidade_pessoas": int(item.quantidade_pessoas or 0),
                "quantidade_vinculos": int(item.quantidade_vinculos or 0),
            }
        )

    return data


def get_siape_ranking(
    db: Session,
    *,
    indicador: SiapeIndicador,
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
    limit: int = 10,
    ordem: SiapeOrdem = "desc",
):
    quantidade_pessoas = func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_pessoas), 0)
    quantidade_vinculos = func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_vinculos), 0)
    indicador_column = quantidade_pessoas if indicador == "quantidade_pessoas" else quantidade_vinculos

    query = db.query(
        FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape.label("codigo_orgao_exercicio_siape"),
        FatoSiapeServidorOrgao.nome_orgao_exercicio_siape.label("nome_orgao_exercicio_siape"),
        FatoSiapeServidorOrgao.codigo_orgao_superior_exercicio_siape.label(
            "codigo_orgao_superior_exercicio_siape"
        ),
        FatoSiapeServidorOrgao.nome_orgao_superior_exercicio_siape.label(
            "nome_orgao_superior_exercicio_siape"
        ),
        quantidade_pessoas.label("quantidade_pessoas"),
        quantidade_vinculos.label("quantidade_vinculos"),
        indicador_column.label("valor"),
    )
    query = _apply_filters(
        query,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )
    query = query.group_by(
        FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape,
        FatoSiapeServidorOrgao.nome_orgao_exercicio_siape,
        FatoSiapeServidorOrgao.codigo_orgao_superior_exercicio_siape,
        FatoSiapeServidorOrgao.nome_orgao_superior_exercicio_siape,
    )

    ordering = asc(indicador_column) if ordem == "asc" else desc(indicador_column)
    items = query.order_by(ordering, FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape.asc()).limit(limit).all()

    return {
        "indicador": indicador,
        "ordem": ordem,
        "codigo_orgao_superior_exercicio": codigo_orgao_superior_exercicio,
        "tipo_servidor": tipo_servidor,
        "tipo_vinculo": tipo_vinculo,
        "situacao": situacao,
        "licenca": licenca,
        "data": [
            {
                "codigo_orgao_exercicio_siape": item.codigo_orgao_exercicio_siape,
                "nome_orgao_exercicio_siape": item.nome_orgao_exercicio_siape,
                "codigo_orgao_superior_exercicio_siape": item.codigo_orgao_superior_exercicio_siape,
                "nome_orgao_superior_exercicio_siape": item.nome_orgao_superior_exercicio_siape,
                "quantidade_pessoas": int(item.quantidade_pessoas or 0),
                "quantidade_vinculos": int(item.quantidade_vinculos or 0),
                "valor": int(item.valor or 0),
            }
            for item in items
        ],
    }


def get_siape_agregacao(
    db: Session,
    *,
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
):
    query = db.query(
        func.count(func.distinct(FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape)).label("quantidade_orgaos"),
        func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_pessoas), 0).label("total_pessoas"),
        func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_vinculos), 0).label("total_vinculos"),
    )
    query = _apply_filters(
        query,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )
    row = query.one()
    return {
        "codigo_orgao_superior_exercicio": codigo_orgao_superior_exercicio,
        "tipo_servidor": tipo_servidor,
        "tipo_vinculo": tipo_vinculo,
        "situacao": situacao,
        "licenca": licenca,
        "quantidade_orgaos": int(row.quantidade_orgaos or 0),
        "total_pessoas": int(row.total_pessoas or 0),
        "total_vinculos": int(row.total_vinculos or 0),
    }


def get_siape_comparativo(
    db: Session,
    *,
    codigos_orgao_exercicio: list[str],
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
):
    normalized_codes = []
    seen_codes: set[str] = set()
    for raw_code in codigos_orgao_exercicio:
        code = str(raw_code).strip()
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)
        normalized_codes.append(code)

    if not normalized_codes:
        raise ValueError("Informe ao menos um codigo de orgao")

    query = db.query(
        FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape.label("codigo_orgao_exercicio_siape"),
        FatoSiapeServidorOrgao.nome_orgao_exercicio_siape.label("nome_orgao_exercicio_siape"),
        FatoSiapeServidorOrgao.codigo_orgao_superior_exercicio_siape.label(
            "codigo_orgao_superior_exercicio_siape"
        ),
        FatoSiapeServidorOrgao.nome_orgao_superior_exercicio_siape.label(
            "nome_orgao_superior_exercicio_siape"
        ),
        func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_pessoas), 0).label("quantidade_pessoas"),
        func.coalesce(func.sum(FatoSiapeServidorOrgao.quantidade_vinculos), 0).label("quantidade_vinculos"),
    ).filter(FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape.in_(normalized_codes))
    query = _apply_filters(
        query,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )
    items = (
        query.group_by(
            FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape,
            FatoSiapeServidorOrgao.nome_orgao_exercicio_siape,
            FatoSiapeServidorOrgao.codigo_orgao_superior_exercicio_siape,
            FatoSiapeServidorOrgao.nome_orgao_superior_exercicio_siape,
        )
        .order_by(FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape.asc())
        .all()
    )

    return {
        "codigo_orgao_superior_exercicio": codigo_orgao_superior_exercicio,
        "tipo_servidor": tipo_servidor,
        "tipo_vinculo": tipo_vinculo,
        "situacao": situacao,
        "licenca": licenca,
        "data": [
            {
                "codigo_orgao_exercicio_siape": item.codigo_orgao_exercicio_siape,
                "nome_orgao_exercicio_siape": item.nome_orgao_exercicio_siape,
                "codigo_orgao_superior_exercicio_siape": item.codigo_orgao_superior_exercicio_siape,
                "nome_orgao_superior_exercicio_siape": item.nome_orgao_superior_exercicio_siape,
                "quantidade_pessoas": int(item.quantidade_pessoas or 0),
                "quantidade_vinculos": int(item.quantidade_vinculos or 0),
            }
            for item in items
        ],
    }


def get_siape_distribuicao(
    db: Session,
    *,
    agrupar_por: SiapeAgrupamento,
    codigo_orgao_exercicio: str | None = None,
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
):
    return {
        "agrupar_por": agrupar_por,
        "codigo_orgao_exercicio": codigo_orgao_exercicio,
        "codigo_orgao_superior_exercicio": codigo_orgao_superior_exercicio,
        "tipo_servidor": tipo_servidor,
        "tipo_vinculo": tipo_vinculo,
        "situacao": situacao,
        "licenca": licenca,
        "data": _build_distribution(
            db,
            agrupar_por=agrupar_por,
            codigo_orgao_exercicio=codigo_orgao_exercicio,
            codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
            tipo_servidor=tipo_servidor,
            tipo_vinculo=tipo_vinculo,
            situacao=situacao,
            licenca=licenca,
        ),
    }


def get_siape_orgao_kpis(
    db: Session,
    *,
    codigo_orgao_exercicio: str,
    codigo_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
):
    query = db.query(FatoSiapeServidorOrgao)
    query = _apply_filters(
        query,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )
    rows = query.order_by(
        FatoSiapeServidorOrgao.sk_situacao.asc(),
        FatoSiapeServidorOrgao.sk_tipo_vinculo.asc(),
        FatoSiapeServidorOrgao.sk_tipo_servidor.asc(),
        FatoSiapeServidorOrgao.licenca.asc(),
    ).all()

    if rows:
        first = rows[0]
        nome_orgao_exercicio = first.nome_orgao_exercicio_siape
        resolved_codigo_superior = first.codigo_orgao_superior_exercicio_siape
        nome_orgao_superior = first.nome_orgao_superior_exercicio_siape
    else:
        nome_orgao_exercicio = None
        resolved_codigo_superior = codigo_orgao_superior_exercicio
        nome_orgao_superior = None

    total_pessoas = sum(int(row.quantidade_pessoas or 0) for row in rows)
    total_vinculos = sum(int(row.quantidade_vinculos or 0) for row in rows)

    return {
        "codigo_orgao_exercicio": codigo_orgao_exercicio,
        "nome_orgao_exercicio": nome_orgao_exercicio,
        "codigo_orgao_superior_exercicio": resolved_codigo_superior,
        "nome_orgao_superior_exercicio": nome_orgao_superior,
        "data": {
            "total_pessoas": total_pessoas,
            "total_vinculos": total_vinculos,
            "total_registros": len(rows),
            "distribuicao_situacao": _build_distribution(
                db,
                agrupar_por="situacao",
                codigo_orgao_exercicio=codigo_orgao_exercicio,
                codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
                tipo_servidor=tipo_servidor,
                tipo_vinculo=tipo_vinculo,
                situacao=situacao,
                licenca=licenca,
            ),
            "distribuicao_tipo_vinculo": _build_distribution(
                db,
                agrupar_por="tipoVinculo",
                codigo_orgao_exercicio=codigo_orgao_exercicio,
                codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
                tipo_servidor=tipo_servidor,
                tipo_vinculo=tipo_vinculo,
                situacao=situacao,
                licenca=licenca,
            ),
            "distribuicao_tipo_servidor": _build_distribution(
                db,
                agrupar_por="tipoServidor",
                codigo_orgao_exercicio=codigo_orgao_exercicio,
                codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
                tipo_servidor=tipo_servidor,
                tipo_vinculo=tipo_vinculo,
                situacao=situacao,
                licenca=licenca,
            ),
            "distribuicao_licenca": _build_distribution(
                db,
                agrupar_por="licenca",
                codigo_orgao_exercicio=codigo_orgao_exercicio,
                codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
                tipo_servidor=tipo_servidor,
                tipo_vinculo=tipo_vinculo,
                situacao=situacao,
                licenca=licenca,
            ),
        },
    }
