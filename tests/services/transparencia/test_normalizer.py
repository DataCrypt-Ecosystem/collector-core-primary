from app.services.transparencia.normalizer import (
    normalize_raw_record,
    normalize_clean_record,
    normalize_siafi_clean_record,
)

def test_normalize_raw_record():
    item = {"codigo": " 123 ", "descricao": " Pagamento ", "extra": "data"}
    pagina = 2
    
    result = normalize_raw_record(item, pagina)
    
    assert result["codigo"] == "123"
    assert result["descricao"] == "Pagamento"
    assert result["pagina_origem"] == 2
    assert result["payload_original_json"] == item

def test_normalize_clean_record_valido():
    item = {"codigo": "456", "descricao": "Auxílio"}
    
    result = normalize_clean_record(item)
    
    assert result["codigo"] == "456"
    assert result["descricao"] == "Auxílio"
    assert result["status_registro"] == "valido"
    assert result["elegivel_dashboard"] is True

def test_normalize_clean_record_invalido():
    item = {"codigo": "000", "descricao": "codigo invalido aqui"}
    
    result = normalize_clean_record(item)
    
    assert result["codigo"] == "000"
    assert result["descricao"] == "codigo invalido aqui"
    assert result["status_registro"] == "invalido"
    assert result["elegivel_dashboard"] is False


def test_normalize_siafi_clean_record_classifies_power_group():
    result = normalize_siafi_clean_record(
        {"codigo": "01000", "descricao": "Camara dos Deputados"}
    )

    assert result["categoria_poder"] == "legislativo"


def test_normalize_siafi_clean_record_defaults_to_pendente():
    result = normalize_siafi_clean_record(
        {"codigo": "99999", "descricao": "Orgao sem identificacao"}
    )

    assert result["categoria_poder"] == "pendente"
