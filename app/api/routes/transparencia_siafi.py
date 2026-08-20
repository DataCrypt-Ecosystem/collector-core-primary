from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transparencia_siafi import (
    SiafiCargaJobItemListResponse,
    SiafiCargaJobListResponse,
    SiafiCargaJobResponse,
    SiafiCargaJobSeedRequest,
    SiafiCargaJobSeedResponse,
    SiafiDespesaOrgaoAgregacaoResponse,
    SiafiDespesaOrgaoComparativoResponse,
    SiafiDespesaOrgaoCollectRequest,
    SiafiDespesaOrgaoCollectResponse,
    SiafiDespesaOrgaoListResponse,
    SiafiDespesaOrgaoRankingResponse,
    SiafiDespesaOrgaoResponse,
    SiafiDespesaOrgaoSerieHistoricaResponse,
    SiafiOrgaoCollectRequest,
    SiafiOrgaoCollectResponse,
    SiafiOrgaoListResponse,
    SiafiOrgaoResponse,
)
from app.services.transparencia.siafi import (
    SiafiCargaJobConflictError,
    SiafiCargaJobNotFoundError,
    collect_siafi_despesas_por_orgao,
    collect_siafi_orgaos,
    delete_siafi_job,
    get_siafi_agregacao,
    get_siafi_comparativo,
    get_siafi_despesa_por_orgao,
    get_siafi_job,
    get_siafi_orgao,
    get_siafi_ranking,
    get_siafi_serie_historica,
    list_siafi_job_items,
    list_siafi_jobs,
    list_siafi_despesas_por_orgao,
    list_siafi_orgaos,
    queue_siafi_job_run,
    reset_siafi_job_to_pending,
    run_siafi_job,
    seed_siafi_jobs,
)

router = APIRouter(prefix="/transparencia/siafi", tags=["Transparencia SIAFI"])


@router.post("/jobs/despesas/por-orgao/seed", response_model=SiafiCargaJobSeedResponse)
def seed_jobs(
    payload: SiafiCargaJobSeedRequest,
    db: Session = Depends(get_db),
):
    created_count, existing_count, jobs = seed_siafi_jobs(
        db,
        anos=payload.anos,
        orgaos=payload.orgaos,
        orgaos_superiores=payload.orgaos_superiores,
        job_code_prefix=payload.job_code_prefix,
        descricao_prefix=payload.descricao_prefix,
    )
    return SiafiCargaJobSeedResponse(
        created_count=created_count,
        existing_count=existing_count,
        jobs=jobs,
    )


@router.get("/jobs", response_model=SiafiCargaJobListResponse)
def get_jobs(
    status: str | None = Query(default=None, min_length=1),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    filter_type: str | None = Query(default=None, alias="filterType", min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = list_siafi_jobs(
        db,
        status=status,
        ano=ano,
        filter_type=filter_type,
        limit=limit,
        offset=offset,
    )
    return SiafiCargaJobListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/jobs/{job_id}", response_model=SiafiCargaJobResponse)
def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = get_siafi_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/items", response_model=SiafiCargaJobItemListResponse)
def get_job_items(
    job_id: int,
    status: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if get_siafi_job(db, job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    total, items = list_siafi_job_items(
        db,
        job_id=job_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return SiafiCargaJobItemListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.post("/jobs/{job_id}/run", response_model=SiafiCargaJobResponse, status_code=202)
def run_job_by_id(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        job = queue_siafi_job_run(db, job_id)
    except SiafiCargaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SiafiCargaJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    background_tasks.add_task(run_siafi_job, job.id)
    return job


@router.post("/jobs/{job_id}/reset-pending", response_model=SiafiCargaJobResponse)
def reset_job_pending_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    try:
        return reset_siafi_job_to_pending(db, job_id)
    except SiafiCargaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SiafiCargaJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    try:
        delete_siafi_job(db, job_id)
    except SiafiCargaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SiafiCargaJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=204)


@router.post("/orgaos/collect", response_model=SiafiOrgaoCollectResponse)
async def collect_orgaos(
    payload: SiafiOrgaoCollectRequest | None = None,
    db: Session = Depends(get_db),
):
    filters = payload or SiafiOrgaoCollectRequest()
    return await collect_siafi_orgaos(
        db,
        codigo=filters.codigo,
        descricao=filters.descricao,
    )


@router.get("/orgaos", response_model=SiafiOrgaoListResponse)
def get_orgaos(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    codigo: str | None = Query(default=None, min_length=1),
    descricao: str | None = Query(default=None, min_length=1),
    status_registro: str | None = Query(default=None, min_length=1),
    elegivel_dashboard: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    total, items = list_siafi_orgaos(
        db,
        limit=limit,
        offset=offset,
        codigo=codigo,
        descricao=descricao,
        status_registro=status_registro,
        elegivel_dashboard=elegivel_dashboard,
    )
    return SiafiOrgaoListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/orgaos/{id}", response_model=SiafiOrgaoResponse)
def get_orgao(
    id: int,
    db: Session = Depends(get_db),
):
    item = get_siafi_orgao(db, id=id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orgao SIAFI not found")
    return item


@router.post("/despesas/por-orgao/collect", response_model=SiafiDespesaOrgaoCollectResponse)
async def collect_despesas_por_orgao(
    payload: SiafiDespesaOrgaoCollectRequest,
    db: Session = Depends(get_db),
):
    try:
        return await collect_siafi_despesas_por_orgao(
            db,
            ano=payload.ano,
            orgao=payload.orgao,
            orgao_superior=payload.orgao_superior,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/despesas/por-orgao", response_model=SiafiDespesaOrgaoListResponse)
def get_despesas_por_orgao(
    ano: int | None = Query(default=None, ge=2000, le=2100),
    codigo_orgao: str | None = Query(default=None, alias="codigoOrgao", min_length=1),
    codigo_orgao_superior: str | None = Query(default=None, alias="codigoOrgaoSuperior", min_length=1),
    orgao: str | None = Query(default=None, min_length=1),
    orgao_superior: str | None = Query(default=None, alias="orgaoSuperior", min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = list_siafi_despesas_por_orgao(
        db,
        ano=ano,
        codigo_orgao=codigo_orgao,
        codigo_orgao_superior=codigo_orgao_superior,
        orgao=orgao,
        orgao_superior=orgao_superior,
        limit=limit,
        offset=offset,
    )
    return SiafiDespesaOrgaoListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/despesas/por-orgao/{id}", response_model=SiafiDespesaOrgaoResponse)
def get_despesa_por_orgao(
    id: int,
    db: Session = Depends(get_db),
):
    item = get_siafi_despesa_por_orgao(db, id=id)
    if item is None:
        raise HTTPException(status_code=404, detail="Despesa SIAFI por orgao not found")
    return item


@router.get(
    "/despesas/por-orgao/analytics/serie-historica",
    response_model=SiafiDespesaOrgaoSerieHistoricaResponse,
)
def get_serie_historica(
    codigo_orgao: str = Query(..., alias="codigoOrgao", min_length=1),
    codigo_orgao_superior: str | None = Query(default=None, alias="codigoOrgaoSuperior", min_length=1),
    db: Session = Depends(get_db),
):
    return get_siafi_serie_historica(
        db,
        codigo_orgao=codigo_orgao,
        codigo_orgao_superior=codigo_orgao_superior,
    )


@router.get(
    "/despesas/por-orgao/analytics/ranking",
    response_model=SiafiDespesaOrgaoRankingResponse,
)
def get_ranking(
    ano: int = Query(..., ge=2000, le=2100),
    indicador: str = Query(..., min_length=1),
    codigo_orgao_superior: str | None = Query(default=None, alias="codigoOrgaoSuperior", min_length=1),
    limit: int = Query(default=10, ge=1, le=100),
    ordem: str = Query(default="desc", min_length=3, max_length=4),
    db: Session = Depends(get_db),
):
    if indicador not in {"empenhado", "liquidado", "pago"}:
        raise HTTPException(status_code=422, detail="Indicador invalido")
    if ordem not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="Ordem invalida")

    return get_siafi_ranking(
        db,
        ano=ano,
        indicador=indicador,
        codigo_orgao_superior=codigo_orgao_superior,
        limit=limit,
        ordem=ordem,
    )


@router.get(
    "/despesas/por-orgao/analytics/agregacao",
    response_model=SiafiDespesaOrgaoAgregacaoResponse,
)
def get_agregacao(
    ano: int = Query(..., ge=2000, le=2100),
    codigo_orgao_superior: str | None = Query(default=None, alias="codigoOrgaoSuperior", min_length=1),
    db: Session = Depends(get_db),
):
    return get_siafi_agregacao(
        db,
        ano=ano,
        codigo_orgao_superior=codigo_orgao_superior,
    )


@router.get(
    "/despesas/por-orgao/analytics/comparativo",
    response_model=SiafiDespesaOrgaoComparativoResponse,
)
def get_comparativo(
    ano: int = Query(..., ge=2000, le=2100),
    codigos_orgao: str = Query(..., alias="codigosOrgao", min_length=1),
    db: Session = Depends(get_db),
):
    try:
        return get_siafi_comparativo(
            db,
            ano=ano,
            codigos_orgao=[value.strip() for value in codigos_orgao.split(",")],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
