from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SiapeOrgaoCollectRequest(BaseModel):
    codigo: str | None = None
    descricao: str | None = None


class SiapeOrgaoCollectResponse(BaseModel):
    tipo_orgao: str
    pages_collected: int
    records_received: int
    raw_inserted: int
    clean_inserted: int
    clean_updated: int


class SiapeOrgaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    descricao: str
    status_registro: str
    elegivel_dashboard: bool
    created_at: datetime
    updated_at: datetime


class SiapeOrgaoListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiapeOrgaoResponse]


class SiapeServidorOrgaoCollectRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    orgao_lotacao: str | None = Field(default=None, alias="orgaoLotacao", min_length=1)
    orgao_exercicio: str | None = Field(default=None, alias="orgaoExercicio", min_length=1)
    tipo_servidor: int | None = Field(default=None, alias="tipoServidor", ge=1, le=2)
    tipo_vinculo: int | None = Field(default=None, alias="tipoVinculo", ge=1, le=4)
    licenca: int | None = Field(default=None, ge=0, le=1)


class SiapeServidorOrgaoCollectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resource: str
    orgao_lotacao: str | None = Field(default=None, alias="orgaoLotacao")
    orgao_exercicio: str | None = Field(default=None, alias="orgaoExercicio")
    tipo_servidor: int | None = Field(default=None, alias="tipoServidor")
    tipo_vinculo: int | None = Field(default=None, alias="tipoVinculo")
    licenca: int | None = None
    pages_collected: int
    records_received: int
    raw_inserted: int
    facts_inserted: int
    facts_updated: int


class SiapeServidorOrgaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_orgao_exercicio_siape: str
    nome_orgao_exercicio_siape: str
    codigo_orgao_superior_exercicio_siape: str
    nome_orgao_superior_exercicio_siape: str
    sk_situacao: int
    desc_situacao: str
    sk_tipo_vinculo: int
    desc_tipo_vinculo: str
    sk_tipo_servidor: int
    desc_tipo_servidor: str
    licenca: int
    quantidade_pessoas: int
    quantidade_vinculos: int
    created_at: datetime
    updated_at: datetime


class SiapeServidorOrgaoListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiapeServidorOrgaoResponse]


class SiapeServidorOrgaoRankingItem(BaseModel):
    codigo_orgao_exercicio_siape: str
    nome_orgao_exercicio_siape: str
    codigo_orgao_superior_exercicio_siape: str
    nome_orgao_superior_exercicio_siape: str
    quantidade_pessoas: int
    quantidade_vinculos: int
    valor: int


class SiapeServidorOrgaoRankingResponse(BaseModel):
    indicador: Literal["quantidade_pessoas", "quantidade_vinculos"]
    ordem: Literal["asc", "desc"]
    codigo_orgao_superior_exercicio: str | None = None
    tipo_servidor: int | None = None
    tipo_vinculo: int | None = None
    situacao: int | None = None
    licenca: int | None = None
    data: list[SiapeServidorOrgaoRankingItem]


class SiapeServidorOrgaoAgregacaoResponse(BaseModel):
    codigo_orgao_superior_exercicio: str | None = None
    tipo_servidor: int | None = None
    tipo_vinculo: int | None = None
    situacao: int | None = None
    licenca: int | None = None
    quantidade_orgaos: int
    total_pessoas: int
    total_vinculos: int


class SiapeServidorOrgaoComparativoItem(BaseModel):
    codigo_orgao_exercicio_siape: str
    nome_orgao_exercicio_siape: str
    codigo_orgao_superior_exercicio_siape: str
    nome_orgao_superior_exercicio_siape: str
    quantidade_pessoas: int
    quantidade_vinculos: int


class SiapeServidorOrgaoComparativoResponse(BaseModel):
    codigo_orgao_superior_exercicio: str | None = None
    tipo_servidor: int | None = None
    tipo_vinculo: int | None = None
    situacao: int | None = None
    licenca: int | None = None
    data: list[SiapeServidorOrgaoComparativoItem]


class SiapeServidorOrgaoDistribuicaoItem(BaseModel):
    chave: str
    descricao: str
    quantidade_orgaos: int
    quantidade_pessoas: int
    quantidade_vinculos: int


class SiapeServidorOrgaoDistribuicaoResponse(BaseModel):
    agrupar_por: Literal["situacao", "tipoVinculo", "tipoServidor", "licenca"]
    codigo_orgao_exercicio: str | None = None
    codigo_orgao_superior_exercicio: str | None = None
    tipo_servidor: int | None = None
    tipo_vinculo: int | None = None
    situacao: int | None = None
    licenca: int | None = None
    data: list[SiapeServidorOrgaoDistribuicaoItem]


class SiapeServidorOrgaoKpiDistribuicaoItem(BaseModel):
    chave: str
    descricao: str
    quantidade_orgaos: int
    quantidade_pessoas: int
    quantidade_vinculos: int


class SiapeServidorOrgaoKpisData(BaseModel):
    total_pessoas: int
    total_vinculos: int
    total_registros: int
    distribuicao_situacao: list[SiapeServidorOrgaoKpiDistribuicaoItem]
    distribuicao_tipo_vinculo: list[SiapeServidorOrgaoKpiDistribuicaoItem]
    distribuicao_tipo_servidor: list[SiapeServidorOrgaoKpiDistribuicaoItem]
    distribuicao_licenca: list[SiapeServidorOrgaoKpiDistribuicaoItem]


class SiapeServidorOrgaoKpisResponse(BaseModel):
    codigo_orgao_exercicio: str
    nome_orgao_exercicio: str | None = None
    codigo_orgao_superior_exercicio: str | None = None
    nome_orgao_superior_exercicio: str | None = None
    data: SiapeServidorOrgaoKpisData
