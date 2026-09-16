from sqlalchemy.orm import Session

from app.models import TransparenciaOrgaoSiafi
from app.services.transparencia.collector import (
    collect_orgaos_siafi as _collect_orgaos_siafi,
    get_orgao_siafi as _get_orgao_siafi,
    list_orgaos_siafi as _list_orgaos_siafi,
)


class SiafiOrgaoNotFoundError(ValueError):
    pass


class SiafiOrgaoCategoryConflictError(ValueError):
    pass


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
    categoria_poder: str | None = None,
):
    return _list_orgaos_siafi(
        db,
        limit=limit,
        offset=offset,
        codigo=codigo,
        descricao=descricao,
        status_registro=status_registro,
        elegivel_dashboard=elegivel_dashboard,
        categoria_poder=categoria_poder,
    )


def get_siafi_orgao(db: Session, id: int):
    return _get_orgao_siafi(db, id=id)


def categorize_siafi_orgao(
    db: Session,
    *,
    orgao_id: int,
    categoria_poder: str,
) -> TransparenciaOrgaoSiafi:
    orgao = db.query(TransparenciaOrgaoSiafi).filter(TransparenciaOrgaoSiafi.id == orgao_id).one_or_none()
    if orgao is None:
        raise SiafiOrgaoNotFoundError("Orgao SIAFI not found")
    if orgao.status_registro != "valido":
        raise SiafiOrgaoCategoryConflictError("Orgao SIAFI nao esta ativo para categorizacao")
    if orgao.categoria_poder != "pendente":
        raise SiafiOrgaoCategoryConflictError("Orgao SIAFI ja foi categorizado")

    orgao.categoria_poder = categoria_poder
    db.commit()
    db.refresh(orgao)
    return orgao
