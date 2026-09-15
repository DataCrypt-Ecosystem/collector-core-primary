from __future__ import annotations

from typing import Any


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def normalize_siape_servidor_orgao_raw_record(
    item: dict[str, Any],
    pagina: int,
    *,
    orgao_lotacao: str | None,
    orgao_exercicio: str | None,
    tipo_servidor: int | None,
    tipo_vinculo: int | None,
    licenca: int | None,
) -> dict[str, Any]:
    return {
        "codigo_orgao_exercicio_siape": _normalize_text(item.get("codOrgaoExercicioSiape")),
        "nome_orgao_exercicio_siape": _normalize_text(item.get("nomOrgaoExercicioSiape")),
        "codigo_orgao_superior_exercicio_siape": _normalize_text(item.get("codOrgaoSuperiorExercicioSiape")),
        "nome_orgao_superior_exercicio_siape": _normalize_text(item.get("nomOrgaoSuperiorExercicioSiape")),
        "sk_situacao": _normalize_int(item.get("skSituacao")),
        "desc_situacao": _normalize_text(item.get("descSituacao")),
        "sk_tipo_vinculo": _normalize_int(item.get("skTipoVinculo")),
        "desc_tipo_vinculo": _normalize_text(item.get("descTipoVinculo")),
        "sk_tipo_servidor": _normalize_int(item.get("skTipoServidor")),
        "desc_tipo_servidor": _normalize_text(item.get("descTipoServidor")),
        "licenca": _normalize_int(item.get("licenca")),
        "pagina_origem": pagina,
        "filtro_orgao_lotacao": _normalize_text(orgao_lotacao),
        "filtro_orgao_exercicio": _normalize_text(orgao_exercicio),
        "filtro_tipo_servidor": _normalize_int(tipo_servidor),
        "filtro_tipo_vinculo": _normalize_int(tipo_vinculo),
        "filtro_licenca": _normalize_int(licenca),
        "payload_original_json": item,
    }


def normalize_siape_servidor_orgao_fact_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "codigo_orgao_exercicio_siape": _normalize_text(item.get("codOrgaoExercicioSiape")),
        "nome_orgao_exercicio_siape": _normalize_text(item.get("nomOrgaoExercicioSiape")),
        "codigo_orgao_superior_exercicio_siape": _normalize_text(item.get("codOrgaoSuperiorExercicioSiape")),
        "nome_orgao_superior_exercicio_siape": _normalize_text(item.get("nomOrgaoSuperiorExercicioSiape")),
        "sk_situacao": _normalize_int(item.get("skSituacao")),
        "desc_situacao": _normalize_text(item.get("descSituacao")),
        "sk_tipo_vinculo": _normalize_int(item.get("skTipoVinculo")),
        "desc_tipo_vinculo": _normalize_text(item.get("descTipoVinculo")),
        "sk_tipo_servidor": _normalize_int(item.get("skTipoServidor")),
        "desc_tipo_servidor": _normalize_text(item.get("descTipoServidor")),
        "licenca": _normalize_int(item.get("licenca")),
        "quantidade_pessoas": _normalize_int(item.get("qntPessoas")),
        "quantidade_vinculos": _normalize_int(item.get("qntVinculos")),
    }
