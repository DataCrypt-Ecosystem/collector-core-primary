from sqlalchemy.orm import Session

from app.services.transparencia.collector import (
    collect_orgaos_siape as _collect_orgaos_siape,
    get_orgao_siape as _get_orgao_siape,
    list_orgaos_siape as _list_orgaos_siape,
)


async def collect_siape_orgaos(
    db: Session,
    *,
    codigo: str | None = None,
    descricao: str | None = None,
):
    return await _collect_orgaos_siape(
        db,
        codigo=codigo,
        descricao=descricao,
    )


def list_siape_orgaos(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
    codigo: str | None = None,
    descricao: str | None = None,
    status_registro: str | None = None,
    elegivel_dashboard: bool | None = None,
):
    return _list_orgaos_siape(
        db,
        limit=limit,
        offset=offset,
        codigo=codigo,
        descricao=descricao,
        status_registro=status_registro,
        elegivel_dashboard=elegivel_dashboard,
    )


def get_siape_orgao(db: Session, id: int):
    return _get_orgao_siape(db, id=id)
