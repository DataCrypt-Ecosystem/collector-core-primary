from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import TransparenciaSiafiCargaJob, TransparenciaSiafiCargaJobItem
from app.services.transparencia.jobs.definitions import (
    ITEM_STATUS_FAILED,
    ITEM_STATUS_PENDING,
    ITEM_STATUS_RUNNING,
    ITEM_STATUS_SUCCESS,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_COMPLETED_WITH_ERRORS,
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
)
from app.services.transparencia.siafi.despesas import collect_siafi_despesas_por_orgao

MAX_JOB_ITEM_ATTEMPTS = int(os.getenv("TRANSPARENCIA_JOB_MAX_ATTEMPTS", "3"))
TIPO_CARGA_SIAFI_DESPESA_ORGAO = "siafi_despesa_orgao"
FILTER_TYPE_ORGAO = "orgao"
FILTER_TYPE_ORGAO_SUPERIOR = "orgao_superior"


class SiafiCargaJobNotFoundError(ValueError):
    pass


class SiafiCargaJobConflictError(ValueError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_codes(values: list[str], label: str) -> list[str]:
    normalized = sorted({str(value).strip() for value in values if str(value).strip()})
    if not normalized:
        raise ValueError(f"{label} nao pode ser vazio")
    return normalized


def _resolve_seed_filters(
    *,
    orgaos: list[str] | None,
    orgaos_superiores: list[str] | None,
) -> tuple[str, list[str]]:
    has_orgaos = bool(orgaos)
    has_orgaos_superiores = bool(orgaos_superiores)
    if has_orgaos == has_orgaos_superiores:
        raise ValueError("Informe orgaos ou orgaosSuperiores, mas nao ambos")

    if has_orgaos:
        return FILTER_TYPE_ORGAO, _normalize_codes(orgaos or [], "orgaos")
    return FILTER_TYPE_ORGAO_SUPERIOR, _normalize_codes(orgaos_superiores or [], "orgaosSuperiores")


def _normalize_years(anos: list[int]) -> list[int]:
    normalized = sorted(set(int(ano) for ano in anos))
    if not normalized:
        raise ValueError("anos nao pode ser vazio")
    if any(ano < 2000 or ano > 2100 for ano in normalized):
        raise ValueError("anos deve conter valores entre 2000 e 2100")
    return normalized


def _build_seed_hash(*parts: str) -> str:
    payload = "|".join(parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]


def _build_job_code(
    *,
    ano: int,
    filter_type: str,
    filter_values: list[str],
    job_code_prefix: str | None,
) -> str:
    prefix = job_code_prefix or "siafi"
    suffix = _build_seed_hash(str(ano), filter_type, *filter_values)
    short_type = "orgao" if filter_type == FILTER_TYPE_ORGAO else "orgao-superior"
    return f"{prefix}-{short_type}-{ano}-{suffix}"


def _build_job_description(
    *,
    ano: int,
    filter_type: str,
    filter_values: list[str],
    descricao_prefix: str | None,
) -> str:
    prefix = descricao_prefix or "Carga SIAFI despesas por orgao"
    label = "orgaos" if filter_type == FILTER_TYPE_ORGAO else "orgaos superiores"
    return f"{prefix} {ano} ({label}: {len(filter_values)})"


def _refresh_job_counts(db: Session, job: TransparenciaSiafiCargaJob) -> TransparenciaSiafiCargaJob:
    rows = (
        db.query(
            TransparenciaSiafiCargaJobItem.status,
            func.count(TransparenciaSiafiCargaJobItem.id),
        )
        .filter(TransparenciaSiafiCargaJobItem.job_id == job.id)
        .group_by(TransparenciaSiafiCargaJobItem.status)
        .all()
    )
    counts = {status: int(count) for status, count in rows}
    job.total_items = int(sum(counts.values()))
    job.pending_items = counts.get(ITEM_STATUS_PENDING, 0)
    job.running_items = counts.get(ITEM_STATUS_RUNNING, 0)
    job.success_items = counts.get(ITEM_STATUS_SUCCESS, 0)
    job.failed_items = counts.get(ITEM_STATUS_FAILED, 0)
    db.commit()
    db.refresh(job)
    return job


def _get_job(db: Session, job_id: int) -> TransparenciaSiafiCargaJob | None:
    return db.query(TransparenciaSiafiCargaJob).filter(TransparenciaSiafiCargaJob.id == job_id).first()


def _get_job_by_code(db: Session, job_code: str) -> TransparenciaSiafiCargaJob | None:
    return db.query(TransparenciaSiafiCargaJob).filter(TransparenciaSiafiCargaJob.job_code == job_code).first()


def _create_job_items(
    db: Session,
    *,
    job: TransparenciaSiafiCargaJob,
    ano: int,
    filter_type: str,
    filter_values: list[str],
) -> None:
    items = [
        TransparenciaSiafiCargaJobItem(
            job_id=job.id,
            ano=ano,
            filter_type=filter_type,
            filter_value=filter_value,
            status=ITEM_STATUS_PENDING,
        )
        for filter_value in filter_values
    ]
    db.add_all(items)


def _filter_jobs(
    jobs: list[TransparenciaSiafiCargaJob],
    *,
    ano: int | None,
    filter_type: str | None,
) -> list[TransparenciaSiafiCargaJob]:
    filtered = jobs
    if ano is not None:
        filtered = [job for job in filtered if int(job.metadata_json.get("ano", 0)) == ano]
    if filter_type is not None:
        filtered = [job for job in filtered if str(job.metadata_json.get("filter_type", "")) == filter_type]
    return filtered


def seed_siafi_jobs(
    db: Session,
    *,
    anos: list[int],
    orgaos: list[str] | None = None,
    orgaos_superiores: list[str] | None = None,
    job_code_prefix: str | None = None,
    descricao_prefix: str | None = None,
) -> tuple[int, int, list[TransparenciaSiafiCargaJob]]:
    normalized_years = _normalize_years(anos)
    filter_type, filter_values = _resolve_seed_filters(
        orgaos=orgaos,
        orgaos_superiores=orgaos_superiores,
    )

    created_count = 0
    existing_count = 0
    jobs: list[TransparenciaSiafiCargaJob] = []

    for ano in normalized_years:
        job_code = _build_job_code(
            ano=ano,
            filter_type=filter_type,
            filter_values=filter_values,
            job_code_prefix=job_code_prefix,
        )
        existing_job = _get_job_by_code(db, job_code)
        if existing_job is not None:
            existing_count += 1
            jobs.append(_refresh_job_counts(db, existing_job))
            continue

        try:
            job = TransparenciaSiafiCargaJob(
                job_code=job_code,
                descricao=_build_job_description(
                    ano=ano,
                    filter_type=filter_type,
                    filter_values=filter_values,
                    descricao_prefix=descricao_prefix,
                ),
                status=JOB_STATUS_PENDING,
                metadata_json={
                    "tipo_carga": TIPO_CARGA_SIAFI_DESPESA_ORGAO,
                    "ano": ano,
                    "filter_type": filter_type,
                    "filter_values": filter_values,
                },
            )
            db.add(job)
            db.flush()
            _create_job_items(
                db,
                job=job,
                ano=ano,
                filter_type=filter_type,
                filter_values=filter_values,
            )
            db.commit()
            db.refresh(job)
        except Exception:
            db.rollback()
            raise

        created_count += 1
        jobs.append(_refresh_job_counts(db, job))

    jobs.sort(key=lambda item: str(item.job_code))
    return created_count, existing_count, jobs


def list_siafi_jobs(
    db: Session,
    *,
    status: str | None = None,
    ano: int | None = None,
    filter_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[TransparenciaSiafiCargaJob]]:
    query = db.query(TransparenciaSiafiCargaJob)
    if status is not None:
        query = query.filter(TransparenciaSiafiCargaJob.status == status)
    jobs = list(
        query.order_by(TransparenciaSiafiCargaJob.created_at.desc(), TransparenciaSiafiCargaJob.id.desc()).all()
    )
    filtered = _filter_jobs(jobs, ano=ano, filter_type=filter_type)
    total = len(filtered)
    return total, filtered[offset : offset + limit]


def get_siafi_job(db: Session, job_id: int) -> TransparenciaSiafiCargaJob | None:
    job = _get_job(db, job_id)
    if job is None:
        return None
    return _refresh_job_counts(db, job)


def list_siafi_job_items(
    db: Session,
    *,
    job_id: int,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[TransparenciaSiafiCargaJobItem]]:
    query = db.query(TransparenciaSiafiCargaJobItem).filter(TransparenciaSiafiCargaJobItem.job_id == job_id)
    if status is not None:
        query = query.filter(TransparenciaSiafiCargaJobItem.status == status)

    total = int(query.count())
    items = (
        query.order_by(
            TransparenciaSiafiCargaJobItem.ano.asc(),
            TransparenciaSiafiCargaJobItem.filter_value.asc(),
            TransparenciaSiafiCargaJobItem.id.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def queue_siafi_job_run(db: Session, job_id: int) -> TransparenciaSiafiCargaJob:
    job = _get_job(db, job_id)
    if job is None:
        raise SiafiCargaJobNotFoundError("Job not found")
    if job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise SiafiCargaJobConflictError("Job is already queued or running")

    job.status = JOB_STATUS_QUEUED
    job.started_at = job.started_at or utcnow()
    job.finished_at = None
    db.commit()
    db.refresh(job)
    return _refresh_job_counts(db, job)


def reset_siafi_job_to_pending(db: Session, job_id: int) -> TransparenciaSiafiCargaJob:
    job = _get_job(db, job_id)
    if job is None:
        raise SiafiCargaJobNotFoundError("Job not found")
    if job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise SiafiCargaJobConflictError("Job is queued or running")

    items = db.query(TransparenciaSiafiCargaJobItem).filter(TransparenciaSiafiCargaJobItem.job_id == job.id).all()
    for item in items:
        item.status = ITEM_STATUS_PENDING
        item.last_error = None
        item.pages_collected = 0
        item.records_received = 0
        item.raw_inserted = 0
        item.facts_inserted = 0
        item.facts_updated = 0
        item.started_at = None
        item.finished_at = None

    job.status = JOB_STATUS_PENDING
    job.started_at = None
    job.finished_at = None
    db.commit()
    db.refresh(job)
    return _refresh_job_counts(db, job)


def delete_siafi_job(db: Session, job_id: int) -> None:
    job = _get_job(db, job_id)
    if job is None:
        raise SiafiCargaJobNotFoundError("Job not found")
    if job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise SiafiCargaJobConflictError("Job is queued or running")
    db.delete(job)
    db.commit()


def _claim_next_job_item(
    db: Session,
    *,
    job_id: int,
    max_attempts: int,
) -> TransparenciaSiafiCargaJobItem | None:
    item = (
        db.query(TransparenciaSiafiCargaJobItem)
        .filter(
            TransparenciaSiafiCargaJobItem.job_id == job_id,
            TransparenciaSiafiCargaJobItem.status == ITEM_STATUS_PENDING,
        )
        .order_by(
            TransparenciaSiafiCargaJobItem.ano.asc(),
            TransparenciaSiafiCargaJobItem.filter_value.asc(),
            TransparenciaSiafiCargaJobItem.id.asc(),
        )
        .first()
    )

    if item is None:
        item = (
            db.query(TransparenciaSiafiCargaJobItem)
            .filter(
                TransparenciaSiafiCargaJobItem.job_id == job_id,
                TransparenciaSiafiCargaJobItem.status == ITEM_STATUS_FAILED,
                TransparenciaSiafiCargaJobItem.attempts < max_attempts,
            )
            .order_by(
                TransparenciaSiafiCargaJobItem.ano.asc(),
                TransparenciaSiafiCargaJobItem.filter_value.asc(),
                TransparenciaSiafiCargaJobItem.id.asc(),
            )
            .first()
        )

    if item is None:
        return None

    item.status = ITEM_STATUS_RUNNING
    item.attempts = int(item.attempts) + 1
    item.started_at = utcnow()
    item.finished_at = None
    db.commit()
    db.refresh(item)
    return item


def _mark_job_item_success(
    db: Session,
    *,
    item_id: int,
    metrics: dict[str, int],
) -> None:
    item = db.query(TransparenciaSiafiCargaJobItem).filter(TransparenciaSiafiCargaJobItem.id == item_id).first()
    if item is None:
        return

    item.status = ITEM_STATUS_SUCCESS
    item.last_error = None
    item.pages_collected = int(metrics["pages_collected"])
    item.records_received = int(metrics["records_received"])
    item.raw_inserted = int(metrics["raw_inserted"])
    item.facts_inserted = int(metrics["facts_inserted"])
    item.facts_updated = int(metrics["facts_updated"])
    item.finished_at = utcnow()
    db.commit()


def _mark_job_item_failed(
    db: Session,
    *,
    item_id: int,
    error_message: str,
) -> None:
    item = db.query(TransparenciaSiafiCargaJobItem).filter(TransparenciaSiafiCargaJobItem.id == item_id).first()
    if item is None:
        return

    item.status = ITEM_STATUS_FAILED
    item.last_error = error_message[:2000]
    item.finished_at = utcnow()
    db.commit()


def _mark_job_running(db: Session, job_id: int) -> TransparenciaSiafiCargaJob | None:
    job = _get_job(db, job_id)
    if job is None:
        return None
    job.status = JOB_STATUS_RUNNING
    job.started_at = job.started_at or utcnow()
    job.finished_at = None
    db.commit()
    db.refresh(job)
    return _refresh_job_counts(db, job)


def _finalize_job(db: Session, job_id: int) -> TransparenciaSiafiCargaJob | None:
    job = _get_job(db, job_id)
    if job is None:
        return None
    job = _refresh_job_counts(db, job)

    if job.pending_items > 0 or job.running_items > 0:
        job.status = JOB_STATUS_FAILED
    elif job.failed_items > 0:
        job.status = JOB_STATUS_COMPLETED_WITH_ERRORS if job.success_items > 0 else JOB_STATUS_FAILED
    else:
        job.status = JOB_STATUS_COMPLETED

    job.finished_at = utcnow()
    db.commit()
    db.refresh(job)
    return _refresh_job_counts(db, job)


def _mark_job_failed(db: Session, job_id: int) -> None:
    job = _get_job(db, job_id)
    if job is None:
        return
    job.status = JOB_STATUS_FAILED
    job.finished_at = utcnow()
    db.commit()


async def run_siafi_job(
    job_id: int,
    *,
    max_attempts: int = MAX_JOB_ITEM_ATTEMPTS,
) -> None:
    db = SessionLocal()
    try:
        job = _mark_job_running(db, job_id)
    finally:
        db.close()

    if job is None:
        return

    try:
        while True:
            db = SessionLocal()
            try:
                item = _claim_next_job_item(db, job_id=job.id, max_attempts=max_attempts)
            finally:
                db.close()

            if item is None:
                break

            try:
                db = SessionLocal()
                try:
                    result = await collect_siafi_despesas_por_orgao(
                        db,
                        ano=int(item.ano),
                        orgao=item.filter_value if item.filter_type == FILTER_TYPE_ORGAO else None,
                        orgao_superior=item.filter_value if item.filter_type == FILTER_TYPE_ORGAO_SUPERIOR else None,
                    )
                finally:
                    db.close()
            except Exception as exc:
                db = SessionLocal()
                try:
                    _mark_job_item_failed(db, item_id=int(item.id), error_message=str(exc))
                finally:
                    db.close()
            else:
                metrics = {
                    "pages_collected": int(result["pages_collected"]),
                    "records_received": int(result["records_received"]),
                    "raw_inserted": int(result["raw_inserted"]),
                    "facts_inserted": int(result["facts_inserted"]),
                    "facts_updated": int(result["facts_updated"]),
                }
                db = SessionLocal()
                try:
                    _mark_job_item_success(db, item_id=int(item.id), metrics=metrics)
                finally:
                    db.close()

        db = SessionLocal()
        try:
            _finalize_job(db, job.id)
        finally:
            db.close()
    except Exception:
        db = SessionLocal()
        try:
            _mark_job_failed(db, job.id)
        finally:
            db.close()
        raise
