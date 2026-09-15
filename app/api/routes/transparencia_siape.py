from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transparencia_siape import (
    SiapeCargaJobItemListResponse,
    SiapeCargaJobListResponse,
    SiapeCargaJobResponse,
    SiapeCargaJobSeedRequest,
    SiapeCargaJobSeedResponse,
    SiapeServidorOrgaoAgregacaoResponse,
    SiapeServidorOrgaoComparativoResponse,
    SiapeOrgaoCollectRequest,
    SiapeOrgaoCollectResponse,
    SiapeOrgaoListResponse,
    SiapeOrgaoResponse,
    SiapeServidorOrgaoCollectRequest,
    SiapeServidorOrgaoCollectResponse,
    SiapeServidorOrgaoDistribuicaoResponse,
    SiapeServidorOrgaoKpisResponse,
    SiapeServidorOrgaoListResponse,
    SiapeServidorOrgaoRankingResponse,
    SiapeServidorOrgaoResponse,
)
from app.services.transparencia.siape import (
    SiapeCargaJobConflictError,
    SiapeCargaJobNotFoundError,
    collect_siape_orgaos,
    collect_siape_servidores_por_orgao,
    delete_siape_job,
    get_siape_agregacao,
    get_siape_comparativo,
    get_siape_distribuicao,
    get_siape_job,
    get_siape_orgao,
    get_siape_orgao_kpis,
    get_siape_ranking,
    get_siape_servidor_por_orgao,
    list_siape_job_items,
    list_siape_jobs,
    list_siape_orgaos,
    list_siape_servidores_por_orgao,
    queue_siape_job_run,
    reset_siape_job_to_pending,
    run_siape_job,
    seed_siape_jobs,
)

router = APIRouter(prefix="/transparencia/siape", tags=["Transparencia SIAPE"])


@router.post("/jobs/servidores/por-orgao/seed", response_model=SiapeCargaJobSeedResponse)
def seed_jobs(
    payload: SiapeCargaJobSeedRequest,
    db: Session = Depends(get_db),
):
    created_count, existing_count, jobs = seed_siape_jobs(
        db,
        orgaos_exercicio=payload.orgaos_exercicio,
        orgaos_lotacao=payload.orgaos_lotacao,
        tipo_servidor=payload.tipo_servidor,
        tipo_vinculo=payload.tipo_vinculo,
        licenca=payload.licenca,
        job_code_prefix=payload.job_code_prefix,
        descricao_prefix=payload.descricao_prefix,
    )
    return SiapeCargaJobSeedResponse(
        created_count=created_count,
        existing_count=existing_count,
        jobs=jobs,
    )


@router.get("/jobs", response_model=SiapeCargaJobListResponse)
def get_jobs(
    status: str | None = Query(default=None, min_length=1),
    filter_type: str | None = Query(default=None, alias="filterType", min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = list_siape_jobs(
        db,
        status=status,
        filter_type=filter_type,
        limit=limit,
        offset=offset,
    )
    return SiapeCargaJobListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/jobs/{job_id}", response_model=SiapeCargaJobResponse)
def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = get_siape_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/items", response_model=SiapeCargaJobItemListResponse)
def get_job_items(
    job_id: int,
    status: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if get_siape_job(db, job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    total, items = list_siape_job_items(
        db,
        job_id=job_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return SiapeCargaJobItemListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.post("/jobs/{job_id}/run", response_model=SiapeCargaJobResponse, status_code=202)
def run_job_by_id(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        job = queue_siape_job_run(db, job_id)
    except SiapeCargaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SiapeCargaJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    background_tasks.add_task(run_siape_job, job.id)
    return job


@router.post("/jobs/{job_id}/reset-pending", response_model=SiapeCargaJobResponse)
def reset_job_pending_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    try:
        return reset_siape_job_to_pending(db, job_id)
    except SiapeCargaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SiapeCargaJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
):
    try:
        delete_siape_job(db, job_id)
    except SiapeCargaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SiapeCargaJobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=204)


@router.post("/orgaos/collect", response_model=SiapeOrgaoCollectResponse)
async def collect_orgaos(
    payload: SiapeOrgaoCollectRequest | None = None,
    db: Session = Depends(get_db),
):
    filters = payload or SiapeOrgaoCollectRequest()
    return await collect_siape_orgaos(
        db,
        codigo=filters.codigo,
        descricao=filters.descricao,
    )


@router.get("/orgaos", response_model=SiapeOrgaoListResponse)
def get_orgaos(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    codigo: str | None = Query(default=None, min_length=1),
    descricao: str | None = Query(default=None, min_length=1),
    status_registro: str | None = Query(default=None, min_length=1),
    elegivel_dashboard: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    total, items = list_siape_orgaos(
        db,
        limit=limit,
        offset=offset,
        codigo=codigo,
        descricao=descricao,
        status_registro=status_registro,
        elegivel_dashboard=elegivel_dashboard,
    )
    return SiapeOrgaoListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/orgaos/{id}", response_model=SiapeOrgaoResponse)
def get_orgao(
    id: int,
    db: Session = Depends(get_db),
):
    item = get_siape_orgao(db, id=id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orgao SIAPE not found")
    return item


@router.post("/servidores/por-orgao/collect", response_model=SiapeServidorOrgaoCollectResponse)
async def collect_servidores_por_orgao(
    payload: SiapeServidorOrgaoCollectRequest,
    db: Session = Depends(get_db),
):
    return await collect_siape_servidores_por_orgao(
        db,
        orgao_lotacao=payload.orgao_lotacao,
        orgao_exercicio=payload.orgao_exercicio,
        tipo_servidor=payload.tipo_servidor,
        tipo_vinculo=payload.tipo_vinculo,
        licenca=payload.licenca,
    )


@router.get("/servidores/por-orgao", response_model=SiapeServidorOrgaoListResponse)
def get_servidores_por_orgao(
    codigo_orgao_exercicio: str | None = Query(default=None, alias="codigoOrgaoExercicio", min_length=1),
    codigo_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="codigoOrgaoSuperiorExercicio",
        min_length=1,
    ),
    nome_orgao_exercicio: str | None = Query(default=None, alias="nomeOrgaoExercicio", min_length=1),
    nome_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="nomeOrgaoSuperiorExercicio",
        min_length=1,
    ),
    tipo_servidor: int | None = Query(default=None, alias="tipoServidor", ge=1, le=2),
    tipo_vinculo: int | None = Query(default=None, alias="tipoVinculo", ge=1, le=4),
    situacao: int | None = Query(default=None, alias="situacao", ge=0),
    licenca: int | None = Query(default=None, ge=0, le=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = list_siape_servidores_por_orgao(
        db,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        nome_orgao_exercicio=nome_orgao_exercicio,
        nome_orgao_superior_exercicio=nome_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
        limit=limit,
        offset=offset,
    )
    return SiapeServidorOrgaoListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/servidores/por-orgao/{id}", response_model=SiapeServidorOrgaoResponse)
def get_servidor_por_orgao(
    id: int,
    db: Session = Depends(get_db),
):
    item = get_siape_servidor_por_orgao(db, id=id)
    if item is None:
        raise HTTPException(status_code=404, detail="Servidor SIAPE por orgao not found")
    return item


@router.get(
    "/servidores/por-orgao/analytics/ranking",
    response_model=SiapeServidorOrgaoRankingResponse,
)
def get_ranking(
    indicador: str = Query(..., min_length=1),
    codigo_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="codigoOrgaoSuperiorExercicio",
        min_length=1,
    ),
    tipo_servidor: int | None = Query(default=None, alias="tipoServidor", ge=1, le=2),
    tipo_vinculo: int | None = Query(default=None, alias="tipoVinculo", ge=1, le=4),
    situacao: int | None = Query(default=None, alias="situacao", ge=0),
    licenca: int | None = Query(default=None, ge=0, le=1),
    limit: int = Query(default=10, ge=1, le=100),
    ordem: str = Query(default="desc", min_length=3, max_length=4),
    db: Session = Depends(get_db),
):
    if indicador not in {"quantidade_pessoas", "quantidade_vinculos"}:
        raise HTTPException(status_code=422, detail="Indicador invalido")
    if ordem not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="Ordem invalida")

    return get_siape_ranking(
        db,
        indicador=indicador,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
        limit=limit,
        ordem=ordem,
    )


@router.get(
    "/servidores/por-orgao/analytics/agregacao",
    response_model=SiapeServidorOrgaoAgregacaoResponse,
)
def get_agregacao(
    codigo_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="codigoOrgaoSuperiorExercicio",
        min_length=1,
    ),
    tipo_servidor: int | None = Query(default=None, alias="tipoServidor", ge=1, le=2),
    tipo_vinculo: int | None = Query(default=None, alias="tipoVinculo", ge=1, le=4),
    situacao: int | None = Query(default=None, alias="situacao", ge=0),
    licenca: int | None = Query(default=None, ge=0, le=1),
    db: Session = Depends(get_db),
):
    return get_siape_agregacao(
        db,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )


@router.get(
    "/servidores/por-orgao/analytics/comparativo",
    response_model=SiapeServidorOrgaoComparativoResponse,
)
def get_comparativo(
    codigos_orgao_exercicio: str = Query(..., alias="codigosOrgaoExercicio", min_length=1),
    codigo_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="codigoOrgaoSuperiorExercicio",
        min_length=1,
    ),
    tipo_servidor: int | None = Query(default=None, alias="tipoServidor", ge=1, le=2),
    tipo_vinculo: int | None = Query(default=None, alias="tipoVinculo", ge=1, le=4),
    situacao: int | None = Query(default=None, alias="situacao", ge=0),
    licenca: int | None = Query(default=None, ge=0, le=1),
    db: Session = Depends(get_db),
):
    try:
        return get_siape_comparativo(
            db,
            codigos_orgao_exercicio=[value.strip() for value in codigos_orgao_exercicio.split(",")],
            codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
            tipo_servidor=tipo_servidor,
            tipo_vinculo=tipo_vinculo,
            situacao=situacao,
            licenca=licenca,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/servidores/por-orgao/analytics/distribuicao",
    response_model=SiapeServidorOrgaoDistribuicaoResponse,
)
def get_distribuicao(
    agrupar_por: str = Query(..., alias="agruparPor", min_length=1),
    codigo_orgao_exercicio: str | None = Query(default=None, alias="codigoOrgaoExercicio", min_length=1),
    codigo_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="codigoOrgaoSuperiorExercicio",
        min_length=1,
    ),
    tipo_servidor: int | None = Query(default=None, alias="tipoServidor", ge=1, le=2),
    tipo_vinculo: int | None = Query(default=None, alias="tipoVinculo", ge=1, le=4),
    situacao: int | None = Query(default=None, alias="situacao", ge=0),
    licenca: int | None = Query(default=None, ge=0, le=1),
    db: Session = Depends(get_db),
):
    if agrupar_por not in {"situacao", "tipoVinculo", "tipoServidor", "licenca"}:
        raise HTTPException(status_code=422, detail="Agrupamento invalido")

    return get_siape_distribuicao(
        db,
        agrupar_por=agrupar_por,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )


@router.get(
    "/servidores/por-orgao/analytics/orgao-kpis",
    response_model=SiapeServidorOrgaoKpisResponse,
)
def get_orgao_kpis(
    codigo_orgao_exercicio: str = Query(..., alias="codigoOrgaoExercicio", min_length=1),
    codigo_orgao_superior_exercicio: str | None = Query(
        default=None,
        alias="codigoOrgaoSuperiorExercicio",
        min_length=1,
    ),
    tipo_servidor: int | None = Query(default=None, alias="tipoServidor", ge=1, le=2),
    tipo_vinculo: int | None = Query(default=None, alias="tipoVinculo", ge=1, le=4),
    situacao: int | None = Query(default=None, alias="situacao", ge=0),
    licenca: int | None = Query(default=None, ge=0, le=1),
    db: Session = Depends(get_db),
):
    return get_siape_orgao_kpis(
        db,
        codigo_orgao_exercicio=codigo_orgao_exercicio,
        codigo_orgao_superior_exercicio=codigo_orgao_superior_exercicio,
        tipo_servidor=tipo_servidor,
        tipo_vinculo=tipo_vinculo,
        situacao=situacao,
        licenca=licenca,
    )
