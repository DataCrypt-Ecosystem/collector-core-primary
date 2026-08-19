from sqlalchemy.orm import Session

from app.services.transparencia.collector import (
    collect_orgaos_siafi as _collect_orgaos_siafi,
    get_orgao_siafi as _get_orgao_siafi,
    list_orgaos_siafi as _list_orgaos_siafi,
)


async def collect_siafi_orgaos(
    db: Session,
    *,
    codigo: str | None = None,
    descricao: str | None = None,
):
    return await _collect_orgaos_siafi(
        db,
        codigo=codigo,
        descricao=descricao,
    )


def list_siafi_orgaos(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
    codigo: str | None = None,
    descricao: str | None = None,
    status_registro: str | None = None,
    elegivel_dashboard: bool | None = None,
):
    return _list_orgaos_siafi(
        db,
        limit=limit,
        offset=offset,
        codigo=codigo,
        descricao=descricao,
        status_registro=status_registro,
        elegivel_dashboard=elegivel_dashboard,
    )


def get_siafi_orgao(db: Session, id: int):
    return _get_orgao_siafi(db, id=id)
