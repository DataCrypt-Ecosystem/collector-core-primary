from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transparencia_siafi import (
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
    collect_siafi_despesas_por_orgao,
    collect_siafi_orgaos,
    get_siafi_agregacao,
    get_siafi_comparativo,
    get_siafi_despesa_por_orgao,
    get_siafi_orgao,
    get_siafi_ranking,
    get_siafi_serie_historica,
    list_siafi_despesas_por_orgao,
    list_siafi_orgaos,
)

router = APIRouter(prefix="/transparencia/siafi", tags=["Transparencia SIAFI"])


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
