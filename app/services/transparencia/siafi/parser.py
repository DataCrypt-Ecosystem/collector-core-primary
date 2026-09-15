from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    normalized = _normalize_text(value).replace(" ", "")
    if not normalized:
        return Decimal("0")

    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetario invalido retornado pelo Portal da Transparencia: {value}") from exc


def normalize_siafi_despesa_orgao_raw_record(item: dict[str, Any], pagina: int) -> dict[str, Any]:
    codigo_orgao = _normalize_text(item.get("codigoOrgao"))
    if not codigo_orgao:
        raise ValueError("Resposta do Portal da Transparencia sem codigoOrgao")

    return {
        "ano": int(item["ano"]),
        "codigo_orgao": codigo_orgao,
        "orgao": _normalize_text(item.get("orgao")),
        "codigo_orgao_superior": _normalize_text(item.get("codigoOrgaoSuperior")),
        "orgao_superior": _normalize_text(item.get("orgaoSuperior")),
        "pagina_origem": pagina,
        "payload_original_json": item,
    }


def normalize_siafi_despesa_orgao_fact_record(item: dict[str, Any]) -> dict[str, Any]:
    codigo_orgao = _normalize_text(item.get("codigoOrgao"))
    if not codigo_orgao:
        raise ValueError("Resposta do Portal da Transparencia sem codigoOrgao")

    return {
        "ano": int(item["ano"]),
        "codigo_orgao": codigo_orgao,
        "orgao": _normalize_text(item.get("orgao")),
        "codigo_orgao_superior": _normalize_text(item.get("codigoOrgaoSuperior")),
        "orgao_superior": _normalize_text(item.get("orgaoSuperior")),
        "empenhado": _normalize_decimal(item.get("empenhado")),
        "liquidado": _normalize_decimal(item.get("liquidado")),
        "pago": _normalize_decimal(item.get("pago")),
    }
