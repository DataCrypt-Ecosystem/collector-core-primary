from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SiafiOrgaoCollectRequest(BaseModel):
    codigo: str | None = None
    descricao: str | None = None


class SiafiOrgaoCollectResponse(BaseModel):
    tipo_orgao: str
    pages_collected: int
    records_received: int
    raw_inserted: int
    clean_inserted: int
    clean_updated: int


class SiafiOrgaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    descricao: str
    status_registro: str
    elegivel_dashboard: bool
    created_at: datetime
    updated_at: datetime


class SiafiOrgaoListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiafiOrgaoResponse]


class SiafiDespesaOrgaoCollectRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ano: int = Field(ge=2000, le=2100)
    orgao: str | None = Field(default=None, min_length=1)
    orgao_superior: str | None = Field(default=None, alias="orgaoSuperior", min_length=1)

    @model_validator(mode="after")
    def validate_filters(self):
        if self.orgao is None and self.orgao_superior is None:
            raise ValueError("Informe orgao ou orgaoSuperior")
        return self


class SiafiDespesaOrgaoCollectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    resource: str
    ano: int
    orgao: str | None = None
    orgao_superior: str | None = Field(default=None, alias="orgaoSuperior")
    pages_collected: int
    records_received: int
    raw_inserted: int
    facts_inserted: int
    facts_updated: int


class SiafiDespesaOrgaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ano: int
    codigo_orgao: str
    orgao: str
    codigo_orgao_superior: str
    orgao_superior: str
    empenhado: Decimal
    liquidado: Decimal
    pago: Decimal
    created_at: datetime
    updated_at: datetime


class SiafiDespesaOrgaoListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiafiDespesaOrgaoResponse]


class SiafiDespesaOrgaoSerieHistoricaItem(BaseModel):
    ano: int
    empenhado: Decimal
    liquidado: Decimal
    pago: Decimal


class SiafiDespesaOrgaoSerieHistoricaResponse(BaseModel):
    codigo_orgao: str
    orgao: str | None = None
    codigo_orgao_superior: str | None = None
    orgao_superior: str | None = None
    data: list[SiafiDespesaOrgaoSerieHistoricaItem]


class SiafiDespesaOrgaoRankingItem(BaseModel):
    codigo_orgao: str
    orgao: str
    codigo_orgao_superior: str
    orgao_superior: str
    valor: Decimal


class SiafiDespesaOrgaoRankingResponse(BaseModel):
    ano: int
    indicador: Literal["empenhado", "liquidado", "pago"]
    ordem: Literal["asc", "desc"]
    codigo_orgao_superior: str | None = None
    data: list[SiafiDespesaOrgaoRankingItem]


class SiafiDespesaOrgaoAgregacaoResponse(BaseModel):
    ano: int
    codigo_orgao_superior: str | None = None
    quantidade_orgaos: int
    total_empenhado: Decimal
    total_liquidado: Decimal
    total_pago: Decimal


class SiafiDespesaOrgaoComparativoItem(BaseModel):
    codigo_orgao: str
    orgao: str
    codigo_orgao_superior: str
    orgao_superior: str
    empenhado: Decimal
    liquidado: Decimal
    pago: Decimal


class SiafiDespesaOrgaoComparativoResponse(BaseModel):
    ano: int
    data: list[SiafiDespesaOrgaoComparativoItem]


class SiafiCargaJobSeedRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    anos: list[int] = Field(min_length=1)
    orgaos: list[str] | None = None
    orgaos_superiores: list[str] | None = Field(default=None, alias="orgaosSuperiores")
    job_code_prefix: str | None = Field(default=None, alias="jobCodePrefix", min_length=1, max_length=50)
    descricao_prefix: str | None = Field(default=None, alias="descricaoPrefix", min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_filters(self):
        self.anos = sorted(set(self.anos))
        if any(ano < 2000 or ano > 2100 for ano in self.anos):
            raise ValueError("anos deve conter valores entre 2000 e 2100")

        has_orgaos = bool(self.orgaos)
        has_orgaos_superiores = bool(self.orgaos_superiores)
        if has_orgaos == has_orgaos_superiores:
            raise ValueError("Informe orgaos ou orgaosSuperiores, mas nao ambos")

        if self.orgaos is not None:
            self.orgaos = sorted({str(value).strip() for value in self.orgaos if str(value).strip()})
            if not self.orgaos:
                raise ValueError("orgaos nao pode ser vazio")

        if self.orgaos_superiores is not None:
            self.orgaos_superiores = sorted(
                {str(value).strip() for value in self.orgaos_superiores if str(value).strip()}
            )
            if not self.orgaos_superiores:
                raise ValueError("orgaosSuperiores nao pode ser vazio")

        return self


class SiafiCargaJobResponse(BaseModel):
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


class SiafiCargaJobListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiafiCargaJobResponse]


class SiafiCargaJobSeedResponse(BaseModel):
    created_count: int
    existing_count: int
    jobs: list[SiafiCargaJobResponse]


class SiafiCargaJobItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    ano: int
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


class SiafiCargaJobItemListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SiafiCargaJobItemResponse]
