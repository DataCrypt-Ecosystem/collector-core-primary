from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import FatoSiapeServidorOrgao, TransparenciaSiapeServidorOrgaoRaw
from app.services.transparencia.client import TransparenciaClient
from app.services.transparencia.jobs.rate_limit import get_shared_portal_request_limiter

from .parser import (
    normalize_siape_servidor_orgao_fact_record,
    normalize_siape_servidor_orgao_raw_record,
)

RESOURCE = "servidores/por-orgao"


def _raw_key(
    row: dict[str, Any],
) -> str:
    parts = [
        row["codigo_orgao_exercicio_siape"],
        row["codigo_orgao_superior_exercicio_siape"],
        str(row["sk_situacao"]),
        str(row["sk_tipo_vinculo"]),
        str(row["sk_tipo_servidor"]),
        str(row["licenca"]),
        row["filtro_orgao_lotacao"],
        row["filtro_orgao_exercicio"],
        str(row["filtro_tipo_servidor"]),
        str(row["filtro_tipo_vinculo"]),
        str(row["filtro_licenca"]),
    ]
    return ":".join(parts)


def _fact_key(
    row: dict[str, Any],
) -> str:
    parts = [
        row["codigo_orgao_exercicio_siape"],
        row["codigo_orgao_superior_exercicio_siape"],
        str(row["sk_situacao"]),
        str(row["sk_tipo_vinculo"]),
        str(row["sk_tipo_servidor"]),
        str(row["licenca"]),
    ]
    return ":".join(parts)


def _filtered_raw_query(
    db: Session,
    *,
    orgao_exercicio: str | None,
    orgao_lotacao: str | None,
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    licenca: int | None,
):
    query = db.query(TransparenciaSiapeServidorOrgaoRaw)
    if orgao_exercicio is not None:
        query = query.filter(TransparenciaSiapeServidorOrgaoRaw.filtro_orgao_exercicio == orgao_exercicio)
    if orgao_lotacao is not None:
        query = query.filter(TransparenciaSiapeServidorOrgaoRaw.filtro_orgao_lotacao == orgao_lotacao)
    if tipo_servidor is not None:
        query = query.filter(TransparenciaSiapeServidorOrgaoRaw.filtro_tipo_servidor == tipo_servidor)
    if tipo_vinculo is not None:
        query = query.filter(TransparenciaSiapeServidorOrgaoRaw.filtro_tipo_vinculo == tipo_vinculo)
    if licenca is not None:
        query = query.filter(TransparenciaSiapeServidorOrgaoRaw.filtro_licenca == licenca)
    return query


def _filtered_fact_query(
    db: Session,
    *,
    codigo_orgao_exercicio: str | None,
    codigo_orgao_superior_exercicio: str | None,
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    situacao: int | None,
    licenca: int | None,
):
    query = db.query(FatoSiapeServidorOrgao)
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


def _load_latest_raw_by_key(
    db: Session,
    *,
    orgao_exercicio: str | None,
    orgao_lotacao: str | None,
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    licenca: int | None,
) -> dict[str, Any]:
    latest_by_key: dict[str, Any] = {}
    items = _filtered_raw_query(
        db,
        orgao_exercicio=orgao_exercicio,
        orgao_lotacao=orgao_lotacao,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        licenca=licenca,
    ).order_by(TransparenciaSiapeServidorOrgaoRaw.id.desc()).all()

    for item in items:
        latest_by_key.setdefault(
            _raw_key(
                {
                    "codigo_orgao_exercicio_siape": item.codigo_orgao_exercicio_siape,
                    "codigo_orgao_superior_exercicio_siape": item.codigo_orgao_superior_exercicio_siape,
                    "sk_situacao": item.sk_situacao,
                    "sk_tipo_vinculo": item.sk_tipo_vinculo,
                    "sk_tipo_servidor": item.sk_tipo_servidor,
                    "licenca": item.licenca,
                    "filtro_orgao_lotacao": item.filtro_orgao_lotacao,
                    "filtro_orgao_exercicio": item.filtro_orgao_exercicio,
                    "filtro_tipo_servidor": item.filtro_tipo_servidor,
                    "filtro_tipo_vinculo": item.filtro_tipo_vinculo,
                    "filtro_licenca": item.filtro_licenca,
                }
            ),
            item,
        )

    return latest_by_key


def _load_fact_by_key(
    db: Session,
    *,
    codigo_orgao_exercicio: str | None,
    codigo_orgao_superior_exercicio: str | None,
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    situacao: int | None,
    licenca: int | None,
) -> dict[str, Any]:
    items = _filtered_fact_query(
        db,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    ).all()

    return {
        _fact_key(
            {
                "codigo_orgao_exercicio_siape": item.codigo_orgao_exercicio_siape,
                "codigo_orgao_superior_exercicio_siape": item.codigo_orgao_superior_exercicio_siape,
                "sk_situacao": item.sk_situacao,
                "sk_tipo_vinculo": item.sk_tipo_vinculo,
                "sk_tipo_servidor": item.sk_tipo_servidor,
                "licenca": item.licenca,
            }
        ): item
        for item in items
    }


def _raw_row_matches(current: Any, row: dict[str, Any]) -> bool:
    return (
        current.codigo_orgao_exercicio_siape == row["codigo_orgao_exercicio_siape"]
        and current.nome_orgao_exercicio_siape == row["nome_orgao_exercicio_siape"]
        and current.codigo_orgao_superior_exercicio_siape == row["codigo_orgao_superior_exercicio_siape"]
        and current.nome_orgao_superior_exercicio_siape == row["nome_orgao_superior_exercicio_siape"]
        and current.sk_situacao == row["sk_situacao"]
        and current.desc_situacao == row["desc_situacao"]
        and current.sk_tipo_vinculo == row["sk_tipo_vinculo"]
        and current.desc_tipo_vinculo == row["desc_tipo_vinculo"]
        and current.sk_tipo_servidor == row["sk_tipo_servidor"]
        and current.desc_tipo_servidor == row["desc_tipo_servidor"]
        and current.licenca == row["licenca"]
        and current.pagina_origem == row["pagina_origem"]
        and current.filtro_orgao_lotacao == row["filtro_orgao_lotacao"]
        and current.filtro_orgao_exercicio == row["filtro_orgao_exercicio"]
        and current.filtro_tipo_servidor == row["filtro_tipo_servidor"]
        and current.filtro_tipo_vinculo == row["filtro_tipo_vinculo"]
        and current.filtro_licenca == row["filtro_licenca"]
        and current.payload_original_json == row["payload_original_json"]
    )


def _fact_row_matches(current: Any, row: dict[str, Any]) -> bool:
    return (
        current.codigo_orgao_exercicio_siape == row["codigo_orgao_exercicio_siape"]
        and current.nome_orgao_exercicio_siape == row["nome_orgao_exercicio_siape"]
        and current.codigo_orgao_superior_exercicio_siape == row["codigo_orgao_superior_exercicio_siape"]
        and current.nome_orgao_superior_exercicio_siape == row["nome_orgao_superior_exercicio_siape"]
        and current.sk_situacao == row["sk_situacao"]
        and current.desc_situacao == row["desc_situacao"]
        and current.sk_tipo_vinculo == row["sk_tipo_vinculo"]
        and current.desc_tipo_vinculo == row["desc_tipo_vinculo"]
        and current.sk_tipo_servidor == row["sk_tipo_servidor"]
        and current.desc_tipo_servidor == row["desc_tipo_servidor"]
        and current.licenca == row["licenca"]
        and current.quantidade_pessoas == row["quantidade_pessoas"]
        and current.quantidade_vinculos == row["quantidade_vinculos"]
    )


def _insert_changed_raw_rows(
    db: Session,
    rows: list[dict[str, Any]],
    *,
    latest_by_key: dict[str, Any],
) -> int:
    inserted = 0

    for row in rows:
        key = _raw_key(row)
        current = latest_by_key.get(key)
        if current is not None and _raw_row_matches(current, row):
            continue

        current = TransparenciaSiapeServidorOrgaoRaw(**row)
        db.add(current)
        latest_by_key[key] = current
        inserted += 1

    db.flush()
    return inserted


def _upsert_fact_rows(
    db: Session,
    rows: list[dict[str, Any]],
    *,
    existing_by_key: dict[str, Any],
) -> tuple[int, int]:
    inserted = 0
    updated = 0

    for row in rows:
        key = _fact_key(row)
        current = existing_by_key.get(key)

        if current is None:
            current = FatoSiapeServidorOrgao(**row)
            db.add(current)
            existing_by_key[key] = current
            inserted += 1
            continue

        if _fact_row_matches(current, row):
            continue

        current.nome_orgao_exercicio_siape = row["nome_orgao_exercicio_siape"]
        current.nome_orgao_superior_exercicio_siape = row["nome_orgao_superior_exercicio_siape"]
        current.desc_situacao = row["desc_situacao"]
        current.desc_tipo_vinculo = row["desc_tipo_vinculo"]
        current.desc_tipo_servidor = row["desc_tipo_servidor"]
        current.quantidade_pessoas = row["quantidade_pessoas"]
        current.quantidade_vinculos = row["quantidade_vinculos"]
        updated += 1

    db.flush()
    return inserted, updated


def _build_collect_summary(
    *,
    orgao_lotacao: str | None,
    orgao_exercicio: str | None,
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    licenca: int | None,
) -> dict[str, Any]:
    return {
        "resource": RESOURCE,
        "orgao_lotacao": orgao_lotacao,
        "orgao_exercicio": orgao_exercicio,
        "tipo_servidor": tipo_servidor,
        "tipo_vinculo": tipo_vinculo,
        "licenca": licenca,
        "pages_collected": 0,
        "records_received": 0,
        "raw_inserted": 0,
        "facts_inserted": 0,
        "facts_updated": 0,
    }


async def collect_siape_servidores_por_orgao(
    db: Session,
    *,
    orgao_lotacao: str | None = None,
    orgao_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    licenca: int | None = None,
):
    summary = _build_collect_summary(
        orgao_lotacao=orgao_lotacao,
        orgao_exercicio=orgao_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        licenca=licenca,
    )
    latest_raw_by_key = _load_latest_raw_by_key(
        db,
        orgao_exercicio=orgao_exercicio,
        orgao_lotacao=orgao_lotacao,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        licenca=licenca,
    )
    existing_by_key = _load_fact_by_key(
        db,
        codigo_orgao_exercicio=orgao_exercicio,
        codigo_orgao_superior_exercicio=None,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=None,
        licenca=licenca,
    )
    limiter = get_shared_portal_request_limiter()

    try:
        async with TransparenciaClient(before_request=limiter.acquire) as client:
            async for pagina, records in client.iter_pages(
                RESOURCE,
                orgaoLotacao=orgao_lotacao,
                orgaoExercicio=orgao_exercicio,
                tipoServidor=tipo_servidor,
                tipoVinculo=tipo_vinculo,
                licenca=licenca,
            ):
                summary["pages_collected"] += 1
                summary["records_received"] += len(records)

                raw_rows = [
                    normalize_siape_servidor_orgao_raw_record(
                        item,
                        pagina,
                        orgao_lotacao=orgao_lotacao,
                        orgao_exercicio=orgao_exercicio,
                        tipo_servidor=tipo_servidor,
                        tipo_vinculo=tipo_vinculo,
                        licenca=licenca,
                    )
                    for item in records
                ]
                summary["raw_inserted"] += _insert_changed_raw_rows(
                    db,
                    raw_rows,
                    latest_by_key=latest_raw_by_key,
                )

                fact_rows = [
                    normalize_siape_servidor_orgao_fact_record(item)
                    for item in records
                ]
                inserted, updated = _upsert_fact_rows(
                    db,
                    fact_rows,
                    existing_by_key=existing_by_key,
                )
                summary["facts_inserted"] += inserted
                summary["facts_updated"] += updated

        db.commit()
    except Exception:
        db.rollback()
        raise

    return summary


def list_siape_servidores_por_orgao(
    db: Session,
    *,
    codigo_orgao_exercicio: str | None = None,
    codigo_orgao_superior_exercicio: str | None = None,
    nome_orgao_exercicio: str | None = None,
    nome_orgao_superior_exercicio: str | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    situacao: int | None = None,
    licenca: int | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = _filtered_fact_query(
        db,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )

    if nome_orgao_exercicio is not None:
        query = query.filter(FatoSiapeServidorOrgao.nome_orgao_exercicio_siape.ilike(f"%{nome_orgao_exercicio}%"))
    if nome_orgao_superior_exercicio is not None:
        query = query.filter(
            FatoSiapeServidorOrgao.nome_orgao_superior_exercicio_siape.ilike(f"%{nome_orgao_superior_exercicio}%")
        )

    total = query.count()
    items = (
        query.order_by(
            FatoSiapeServidorOrgao.codigo_orgao_exercicio_siape.asc(),
            FatoSiapeServidorOrgao.sk_tipo_servidor.asc(),
            FatoSiapeServidorOrgao.sk_tipo_vinculo.asc(),
            FatoSiapeServidorOrgao.sk_situacao.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, items


def get_siape_servidor_por_orgao(db: Session, id: int):
    return db.query(FatoSiapeServidorOrgao).filter(FatoSiapeServidorOrgao.id == id).one_or_none()
