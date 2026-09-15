from app.services.transparencia.filters import (
    classify_categoria_poder,
    classify_registro,
    is_dashboard_eligible,
)


def normalize_raw_record(item: dict, pagina_origem: int) -> dict:
    codigo = str(item.get("codigo", "")).strip()
    descricao = str(item.get("descricao", "")).strip()

    return {
        "codigo": codigo,
        "descricao": descricao,
        "pagina_origem": pagina_origem,
        "payload_original_json": item,
    }


def normalize_clean_record(item: dict) -> dict:
    codigo = str(item.get("codigo", "")).strip()
    descricao = str(item.get("descricao", "")).strip()
    status_registro = classify_registro(descricao)

    return {
        "codigo": codigo,
        "descricao": descricao,
        "status_registro": status_registro,
        "elegivel_dashboard": is_dashboard_eligible(status_registro),
    }


def normalize_siafi_clean_record(item: dict) -> dict:
    row = normalize_clean_record(item)
    row["categoria_poder"] = classify_categoria_poder(row["descricao"])
    return row
