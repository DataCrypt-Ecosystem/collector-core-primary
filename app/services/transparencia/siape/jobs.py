from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import TransparenciaSiapeCargaJob, TransparenciaSiapeCargaJobItem
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
from app.services.transparencia.siape.servidores import collect_siape_servidores_por_orgao

MAX_JOB_ITEM_ATTEMPTS = int(os.getenv("TRANSPARENCIA_JOB_MAX_ATTEMPTS", "3"))
TIPO_CARGA_SIAPE_SERVIDOR_ORGAO = "siape_servidor_orgao"
FILTER_TYPE_ORGAO_EXERCICIO = "orgao_exercicio"
FILTER_TYPE_ORGAO_LOTACAO = "orgao_lotacao"


class SiapeCargaJobNotFoundError(ValueError):
    pass


class SiapeCargaJobConflictError(ValueError):
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
    orgaos_exercicio: list[str] | None,
    orgaos_lotacao: list[str] | None,
) -> tuple[str, list[str]]:
    has_orgaos_exercicio = bool(orgaos_exercicio)
    has_orgaos_lotacao = bool(orgaos_lotacao)
    if has_orgaos_exercicio == has_orgaos_lotacao:
        raise ValueError("Informe orgaosExercicio ou orgaosLotacao, mas nao ambos")

    if has_orgaos_exercicio:
        return FILTER_TYPE_ORGAO_EXERCICIO, _normalize_codes(orgaos_exercicio or [], "orgaosExercicio")
    return FILTER_TYPE_ORGAO_LOTACAO, _normalize_codes(orgaos_lotacao or [], "orgaosLotacao")


def _build_seed_hash(*parts: str) -> str:
    payload = "|".join(parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]


def _build_job_code(
    *,
    filter_type: str,
    filter_values: list[str],
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    licenca: int | None,
    job_code_prefix: str | None,
) -> str:
    prefix = job_code_prefix or "siape"
    suffix = _build_seed_hash(
        filter_type,
        *(filter_values),
        str(tipo_servidor or ""),
        str(tipo_vinculo or ""),
        str(licenca if licenca is not None else ""),
    )
    short_type = "exercicio" if filter_type == FILTER_TYPE_ORGAO_EXERCICIO else "lotacao"
    return f"{prefix}-{short_type}-{suffix}"


def _build_job_description(
    *,
    filter_type: str,
    filter_values: list[str],
    descricao_prefix: str | None,
) -> str:
    prefix = descricao_prefix or "Carga SIAPE servidores por orgao"
    label = "orgaos exercicio" if filter_type == FILTER_TYPE_ORGAO_EXERCICIO else "orgaos lotacao"
    return f"{prefix} ({label}: {len(filter_values)})"


def _refresh_job_counts(db: Session, job: TransparenciaSiapeCargaJob) -> TransparenciaSiapeCargaJob:
    rows = (
        db.query(
            TransparenciaSiapeCargaJobItem.status,
            func.count(TransparenciaSiapeCargaJobItem.id),
        )
        .filter(TransparenciaSiapeCargaJobItem.job_id == job.id)
        .group_by(TransparenciaSiapeCargaJobItem.status)
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


def _get_job(db: Session, job_id: int) -> TransparenciaSiapeCargaJob | None:
    return db.query(TransparenciaSiapeCargaJob).filter(TransparenciaSiapeCargaJob.id == job_id).first()


def _get_job_by_code(db: Session, job_code: str) -> TransparenciaSiapeCargaJob | None:
    return db.query(TransparenciaSiapeCargaJob).filter(TransparenciaSiapeCargaJob.job_code == job_code).first()


def _create_job_items(
    db: Session,
    *,
    job: TransparenciaSiapeCargaJob,
    filter_type: str,
    filter_values: list[str],
) -> None:
    items = [
        TransparenciaSiapeCargaJobItem(
            job_id=job.id,
            filter_type=filter_type,
            filter_value=filter_value,
            status=ITEM_STATUS_PENDING,
        )
        for filter_value in filter_values
    ]
    db.add_all(items)


def seed_siape_jobs(
    db: Session,
    *,
    orgaos_exercicio: list[str] | None = None,
    orgaos_lotacao: list[str] | None = None,
    tipo_servidor: int | None = None,
    tipo_vinculo: int | None = None,
    licenca: int | None = None,
    job_code_prefix: str | None = None,
    descricao_prefix: str | None = None,
) -> tuple[int, int, list[TransparenciaSiapeCargaJob]]:
    filter_type, filter_values = _resolve_seed_filters(
        orgaos_exercicio=orgaos_exercicio,
        orgaos_lotacao=orgaos_lotacao,
    )
    job_code = _build_job_code(
        filter_type=filter_type,
        filter_values=filter_values,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        licenca=licenca,
        job_code_prefix=job_code_prefix,
    )
    existing_job = _get_job_by_code(db, job_code)
    if existing_job is not None:
        return 0, 1, [_refresh_job_counts(db, existing_job)]

    try:
        job = TransparenciaSiapeCargaJob(
            job_code=job_code,
            descricao=_build_job_description(
                filter_type=filter_type,
                filter_values=filter_values,
                descricao_prefix=descricao_prefix,
            ),
            status=JOB_STATUS_PENDING,
            metadata_json={
                "tipo_carga": TIPO_CARGA_SIAPE_SERVIDOR_ORGAO,
                "filter_type": filter_type,
                "filter_values": filter_values,
                "tipo_servidor": tipo_servidor,
                "tipo_vinculo": tipo_vinculo,
                "licenca": licenca,
            },
        )
        db.add(job)
        db.flush()
        _create_job_items(
            db,
            job=job,
            filter_type=filter_type,
            filter_values=filter_values,
        )
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return 1, 0, [_refresh_job_counts(db, job)]


def list_siape_jobs(
    db: Session,
    *,
    status: str | None = None,
    filter_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[TransparenciaSiapeCargaJob]]:
    query = db.query(TransparenciaSiapeCargaJob)
    if status is not None:
        query = query.filter(TransparenciaSiapeCargaJob.status == status)
    jobs = list(
        query.order_by(TransparenciaSiapeCargaJob.created_at.desc(), TransparenciaSiapeCargaJob.id.desc()).all()
    )
    if filter_type is not None:
        jobs = [job for job in jobs if str(job.metadata_json.get("filter_type", "")) == filter_type]
    total = len(jobs)
    return total, jobs[offset : offset + limit]


def get_siape_job(db: Session, job_id: int) -> TransparenciaSiapeCargaJob | None:
    job = _get_job(db, job_id)
    if job is None:
        return None
    return _refresh_job_counts(db, job)


def list_siape_job_items(
    db: Session,
    *,
    job_id: int,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[TransparenciaSiapeCargaJobItem]]:
    query = db.query(TransparenciaSiapeCargaJobItem).filter(TransparenciaSiapeCargaJobItem.job_id == job_id)
    if status is not None:
        query = query.filter(TransparenciaSiapeCargaJobItem.status == status)

    total = int(query.count())
    items = (
        query.order_by(
            TransparenciaSiapeCargaJobItem.filter_value.asc(),
            TransparenciaSiapeCargaJobItem.id.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def queue_siape_job_run(db: Session, job_id: int) -> TransparenciaSiapeCargaJob:
    job = _get_job(db, job_id)
    if job is None:
        raise SiapeCargaJobNotFoundError("Job not found")
    if job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise SiapeCargaJobConflictError("Job is already queued or running")

    job.status = JOB_STATUS_QUEUED
    job.started_at = job.started_at or utcnow()
    job.finished_at = None
    db.commit()
    db.refresh(job)
    return _refresh_job_counts(db, job)


def reset_siape_job_to_pending(db: Session, job_id: int) -> TransparenciaSiapeCargaJob:
    job = _get_job(db, job_id)
    if job is None:
        raise SiapeCargaJobNotFoundError("Job not found")
    if job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise SiapeCargaJobConflictError("Job is queued or running")

    items = db.query(TransparenciaSiapeCargaJobItem).filter(TransparenciaSiapeCargaJobItem.job_id == job.id).all()
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


def delete_siape_job(db: Session, job_id: int) -> None:
    job = _get_job(db, job_id)
    if job is None:
        raise SiapeCargaJobNotFoundError("Job not found")
    if job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise SiapeCargaJobConflictError("Job is queued or running")
    db.delete(job)
    db.commit()


def _claim_next_job_item(
    db: Session,
    *,
    job_id: int,
    max_attempts: int,
) -> TransparenciaSiapeCargaJobItem | None:
    item = (
        db.query(TransparenciaSiapeCargaJobItem)
        .filter(
            TransparenciaSiapeCargaJobItem.job_id == job_id,
            TransparenciaSiapeCargaJobItem.status == ITEM_STATUS_PENDING,
        )
        .order_by(
            TransparenciaSiapeCargaJobItem.filter_value.asc(),
            TransparenciaSiapeCargaJobItem.id.asc(),
        )
        .first()
    )

    if item is None:
        item = (
            db.query(TransparenciaSiapeCargaJobItem)
            .filter(
                TransparenciaSiapeCargaJobItem.job_id == job_id,
                TransparenciaSiapeCargaJobItem.status == ITEM_STATUS_FAILED,
                TransparenciaSiapeCargaJobItem.attempts < max_attempts,
            )
            .order_by(
                TransparenciaSiapeCargaJobItem.filter_value.asc(),
                TransparenciaSiapeCargaJobItem.id.asc(),
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
    item = db.query(TransparenciaSiapeCargaJobItem).filter(TransparenciaSiapeCargaJobItem.id == item_id).first()
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
    item = db.query(TransparenciaSiapeCargaJobItem).filter(TransparenciaSiapeCargaJobItem.id == item_id).first()
    if item is None:
        return

    item.status = ITEM_STATUS_FAILED
    item.last_error = error_message[:2000]
    item.finished_at = utcnow()
    db.commit()


def _mark_job_running(db: Session, job_id: int) -> TransparenciaSiapeCargaJob | None:
    job = _get_job(db, job_id)
    if job is None:
        return None
    job.status = JOB_STATUS_RUNNING
    job.started_at = job.started_at or utcnow()
    job.finished_at = None
    db.commit()
    db.refresh(job)
    return _refresh_job_counts(db, job)


def _finalize_job(db: Session, job_id: int) -> TransparenciaSiapeCargaJob | None:
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


async def run_siape_job(
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

    tipo_servidor = job.metadata_json.get("tipo_servidor")
    tipo_vinculo = job.metadata_json.get("tipo_vinculo")
    licenca = job.metadata_json.get("licenca")

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
                    result = await collect_siape_servidores_por_orgao(
                        db,
                        orgao_lotacao=item.filter_value if item.filter_type == FILTER_TYPE_ORGAO_LOTACAO else None,
                        orgao_exercicio=item.filter_value if item.filter_type == FILTER_TYPE_ORGAO_EXERCICIO else None,
                        tipo_servidor=int(tipo_servidor) if tipo_servidor is not None else None,
                        tipo_vinculo=int(tipo_vinculo) if tipo_vinculo is not None else None,
                        licenca=int(licenca) if licenca is not None else None,
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
