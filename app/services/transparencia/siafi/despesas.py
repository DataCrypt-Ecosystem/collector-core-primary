from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import FatoSiafiDespesaOrgaoAnual, TransparenciaSiafiDespesaOrgaoRaw
from app.services.transparencia.client import TransparenciaClient
from app.services.transparencia.jobs.rate_limit import get_shared_portal_request_limiter

from .parser import (
    normalize_siafi_despesa_orgao_fact_record,
    normalize_siafi_despesa_orgao_raw_record,
)

RESOURCE = "despesas/por-orgao"


def _logical_key(ano: int, codigo_orgao: str, codigo_orgao_superior: str) -> str:
    return f"{ano}:{codigo_orgao}:{codigo_orgao_superior}"


def _validate_filters(ano: int, orgao: str | None, orgao_superior: str | None) -> None:
    if ano < 2000 or ano > 2100:
        raise ValueError("Ano invalido")
    if orgao is None and orgao_superior is None:
        raise ValueError("Informe orgao ou orgaoSuperior")


def _filtered_raw_query(
    db: Session,
    *,
    ano: int,
    orgao: str | None,
    orgao_superior: str | None,
):
    query = db.query(TransparenciaSiafiDespesaOrgaoRaw).filter(
        TransparenciaSiafiDespesaOrgaoRaw.ano == ano
    )
    if orgao is not None:
        query = query.filter(TransparenciaSiafiDespesaOrgaoRaw.codigo_orgao == orgao)
    if orgao_superior is not None:
        query = query.filter(TransparenciaSiafiDespesaOrgaoRaw.codigo_orgao_superior == orgao_superior)
    return query


def _filtered_fact_query(
    db: Session,
    *,
    ano: int,
    orgao: str | None,
    orgao_superior: str | None,
):
    query = db.query(FatoSiafiDespesaOrgaoAnual).filter(
        FatoSiafiDespesaOrgaoAnual.ano == ano
    )
    if orgao is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.codigo_orgao == orgao)
    if orgao_superior is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.codigo_orgao_superior == orgao_superior)
    return query


def _load_latest_raw_by_key(
    db: Session,
    *,
    ano: int,
    orgao: str | None,
    orgao_superior: str | None,
) -> dict[str, Any]:
    latest_by_key: dict[str, Any] = {}
    items = _filtered_raw_query(
        db,
        ano=ano,
        orgao=orgao,
        orgao_superior=orgao_superior,
    ).order_by(TransparenciaSiafiDespesaOrgaoRaw.id.desc()).all()

    for item in items:
        latest_by_key.setdefault(
            _logical_key(item.ano, item.codigo_orgao, item.codigo_orgao_superior),
            item,
        )

    return latest_by_key


def _load_fact_by_key(
    db: Session,
    *,
    ano: int,
    orgao: str | None,
    orgao_superior: str | None,
) -> dict[str, Any]:
    items = _filtered_fact_query(
        db,
        ano=ano,
        orgao=orgao,
        orgao_superior=orgao_superior,
    ).all()
    return {
        _logical_key(item.ano, item.codigo_orgao, item.codigo_orgao_superior): item
        for item in items
    }


def _raw_row_matches(current: Any, row: dict[str, Any]) -> bool:
    return (
        current.ano == row["ano"]
        and current.codigo_orgao == row["codigo_orgao"]
        and current.orgao == row["orgao"]
        and current.codigo_orgao_superior == row["codigo_orgao_superior"]
        and current.orgao_superior == row["orgao_superior"]
        and current.pagina_origem == row["pagina_origem"]
        and current.payload_original_json == row["payload_original_json"]
    )


def _fact_row_matches(current: Any, row: dict[str, Any]) -> bool:
    return (
        current.ano == row["ano"]
        and current.codigo_orgao == row["codigo_orgao"]
        and current.orgao == row["orgao"]
        and current.codigo_orgao_superior == row["codigo_orgao_superior"]
        and current.orgao_superior == row["orgao_superior"]
        and current.empenhado == row["empenhado"]
        and current.liquidado == row["liquidado"]
        and current.pago == row["pago"]
    )


def _insert_changed_raw_rows(
    db: Session,
    rows: list[dict[str, Any]],
    *,
    latest_by_key: dict[str, Any],
) -> int:
    inserted = 0

    for row in rows:
        key = _logical_key(row["ano"], row["codigo_orgao"], row["codigo_orgao_superior"])
        current = latest_by_key.get(key)
        if current is not None and _raw_row_matches(current, row):
            continue

        current = TransparenciaSiafiDespesaOrgaoRaw(**row)
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
        key = _logical_key(row["ano"], row["codigo_orgao"], row["codigo_orgao_superior"])
        current = existing_by_key.get(key)

        if current is None:
            current = FatoSiafiDespesaOrgaoAnual(**row)
            db.add(current)
            existing_by_key[key] = current
            inserted += 1
            continue

        if _fact_row_matches(current, row):
            continue

        current.orgao = row["orgao"]
        current.orgao_superior = row["orgao_superior"]
        current.empenhado = row["empenhado"]
        current.liquidado = row["liquidado"]
        current.pago = row["pago"]
        updated += 1

    db.flush()
    return inserted, updated


def _build_collect_summary(
    *,
    ano: int,
    orgao: str | None,
    orgao_superior: str | None,
) -> dict[str, Any]:
    return {
        "resource": RESOURCE,
        "ano": ano,
        "orgao": orgao,
        "orgao_superior": orgao_superior,
        "pages_collected": 0,
        "records_received": 0,
        "raw_inserted": 0,
        "facts_inserted": 0,
        "facts_updated": 0,
    }


async def collect_siafi_despesas_por_orgao(
    db: Session,
    *,
    ano: int,
    orgao: str | None = None,
    orgao_superior: str | None = None,
):
    _validate_filters(ano, orgao, orgao_superior)
    summary = _build_collect_summary(
        ano=ano,
        orgao=orgao,
        orgao_superior=orgao_superior,
    )
    latest_raw_by_key = _load_latest_raw_by_key(
        db,
        ano=ano,
        orgao=orgao,
        orgao_superior=orgao_superior,
    )
    existing_by_key = _load_fact_by_key(
        db,
        ano=ano,
        orgao=orgao,
        orgao_superior=orgao_superior,
    )
    limiter = get_shared_portal_request_limiter()

    try:
        async with TransparenciaClient(before_request=limiter.acquire) as client:
            async for pagina, records in client.iter_pages(
                RESOURCE,
                ano=ano,
                orgao=orgao,
                orgaoSuperior=orgao_superior,
            ):
                summary["pages_collected"] += 1
                summary["records_received"] += len(records)

                raw_rows = [
                    normalize_siafi_despesa_orgao_raw_record(item, pagina)
                    for item in records
                ]
                summary["raw_inserted"] += _insert_changed_raw_rows(
                    db,
                    raw_rows,
                    latest_by_key=latest_raw_by_key,
                )

                fact_rows = [
                    normalize_siafi_despesa_orgao_fact_record(item)
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


def list_siafi_despesas_por_orgao(
    db: Session,
    *,
    ano: int | None = None,
    codigo_orgao: str | None = None,
    codigo_orgao_superior: str | None = None,
    orgao: str | None = None,
    orgao_superior: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = db.query(FatoSiafiDespesaOrgaoAnual)

    if ano is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.ano == ano)
    if codigo_orgao is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.codigo_orgao == codigo_orgao)
    if codigo_orgao_superior is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.codigo_orgao_superior == codigo_orgao_superior)
    if orgao is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.orgao.ilike(f"%{orgao}%"))
    if orgao_superior is not None:
        query = query.filter(FatoSiafiDespesaOrgaoAnual.orgao_superior.ilike(f"%{orgao_superior}%"))

    total = query.count()
    items = (
        query.order_by(
            FatoSiafiDespesaOrgaoAnual.ano.desc(),
            FatoSiafiDespesaOrgaoAnual.codigo_orgao.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, items


def get_siafi_despesa_por_orgao(db: Session, id: int):
    return (
        db.query(FatoSiafiDespesaOrgaoAnual)
        .filter(FatoSiafiDespesaOrgaoAnual.id == id)
        .one_or_none()
    )
