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
