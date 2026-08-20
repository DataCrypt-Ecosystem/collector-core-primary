from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class SiapeCargaJobSeedRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    orgaos_exercicio: list[str] | None = Field(default=None, alias="orgaosExercicio")
    orgaos_lotacao: list[str] | None = Field(default=None, alias="orgaosLotacao")
    tipo_servidor: int | None = Field(default=None, alias="tipoServidor", ge=1, le=2)
    tipo_vinculo: int | None = Field(default=None, alias="tipoVinculo", ge=1, le=4)
    licenca: int | None = Field(default=None, ge=0, le=1)
    job_code_prefix: str | None = Field(default=None, alias="jobCodePrefix", min_length=1, max_length=50)
    descricao_prefix: str | None = Field(default=None, alias="descricaoPrefix", min_length=1, max_length=100)

    @staticmethod
    def _normalize_codes(values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized = sorted({str(value).strip() for value in values if str(value).strip()})
        return normalized or None

    @property
    def filter_type(self) -> str:
        return "orgao_exercicio" if self.orgaos_exercicio else "orgao_lotacao"

    @property
    def filter_values(self) -> list[str]:
        return self.orgaos_exercicio or self.orgaos_lotacao or []

    @model_validator(mode="after")
    def validate_filters(self):
        self.orgaos_exercicio = self._normalize_codes(self.orgaos_exercicio)
        self.orgaos_lotacao = self._normalize_codes(self.orgaos_lotacao)

        has_orgaos_exercicio = bool(self.orgaos_exercicio)
        has_orgaos_lotacao = bool(self.orgaos_lotacao)
        if has_orgaos_exercicio == has_orgaos_lotacao:
            raise ValueError("Informe orgaosExercicio ou orgaosLotacao, mas nao ambos")

        return self


class SiapeCargaJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_code: str
    descricao: str
    status: str
    metadata_json: dict
    total_items: int
    pending_items: int
    running_items: int
    success_items: int
    failed_items: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class SiapeCargaJobListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiapeCargaJobResponse]


class SiapeCargaJobSeedResponse(BaseModel):
    created_count: int
    existing_count: int
    jobs: list[SiapeCargaJobResponse]


class SiapeCargaJobItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    filter_type: str
    filter_value: str
    status: str
    attempts: int
    last_error: str | None
    pages_collected: int
    records_received: int
    raw_inserted: int
    facts_inserted: int
    facts_updated: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class SiapeCargaJobItemListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiapeCargaJobItemResponse]
