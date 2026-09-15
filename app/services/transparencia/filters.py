import unicodedata


def classify_registro(descricao: str) -> str:
    descricao_normalizada = descricao.strip()
    descricao_upper = descricao_normalizada.upper()

    if "CODIGO INVALIDO" in descricao_upper:
        return "invalido"
    if descricao_normalizada.startswith("Exc -"):
        return "excecao"
    if descricao_upper.startswith("IGNORADO"):
        return "ignorado"
    return "valido"


def is_dashboard_eligible(status_registro: str) -> bool:
    return status_registro == "valido"


def classify_categoria_poder(descricao: str) -> str:
    """Classifica o órgão por grupo institucional a partir da descrição SIAFI.

    A classificação é deliberadamente conservadora: quando a descrição não
    identifica o grupo com segurança, o registro fica em ``pendente`` para
    revisão posterior.
    """
    normalized = unicodedata.normalize("NFKD", descricao.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))

    if "tribunal de contas" in normalized:
        return "controle_externo"
    if "ministerio publico" in normalized or "procuradoria-geral da republica" in normalized:
        return "ministerio_publico"
    if "defensoria publica" in normalized:
        return "defensoria_publica"
    if "advocacia-geral da uniao" in normalized:
        return "advocacia_publica"
    if any(
        term in normalized
        for term in (
            "supremo tribunal federal",
            "superior tribunal de justica",
            "tribunal superior",
            "justica federal",
            "justica do trabalho",
            "justica eleitoral",
            "justica militar",
            "conselho nacional de justica",
        )
    ):
        return "judiciario"
    if "camara dos deputados" in normalized or "senado federal" in normalized:
        return "legislativo"
    if any(
        term in normalized
        for term in (
            "presidencia da republica",
            "vice-presidencia da republica",
            "ministerio ",
            "comando do exercito",
            "comando da marinha",
            "comando da aeronautica",
        )
    ):
        return "executivo"
    return "pendente"
